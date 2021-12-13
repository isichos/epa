# from bootstrap_modal_forms.generic import BSModalCreateView
from django.contrib.auth.decorators import login_required
import json
import logging
from django.http import HttpResponseForbidden, JsonResponse
from django.http.response import Http404
from django.shortcuts import *
from django.urls import reverse, reverse_lazy
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from jsonview.decorators import json_view
from crispy_forms.templatetags import crispy_forms_filters
from datetime import datetime
from users.models import CustomUser
from django.db.models import Q
from .forms import *
from .requests import mvs_simulation_request
from .models import *
from .scenario_topology_helpers import handle_storage_unit_form_post, handle_bus_form_post, handle_asset_form_post, create_node_interconnection_links, load_scenario_topology_from_db, NodeObject, \
    update_deleted_objects_from_database, duplicate_scenario_objects, duplicate_scenario_connections, get_topology_json
from .services import create_or_delete_simulation_scheduler, send_feedback_email
from .constants import DONE, ERROR
logger = logging.getLogger(__name__)

# region Project

@login_required
@require_http_methods(["GET", "POST"])
def user_feedback(request):
    form = FeedbackForm(request.POST or None)
    if request.POST:
        if form.is_valid():
            feedback = form.save(commit=False)
            try:
                feedback.rating = [key.split('-')[-1] for key in request.POST.keys() if key.startswith('rating')][0]
            except:
                feedback.rating = None
            feedback.save()
            subject = f"[E-LAND] [EPA] Feedback for EPA - {feedback.subject}"
            body = f"Feedback form for Energy Planning Application\n\nReceived Feedback\n-----------------\n\nTopic: {feedback.subject}\nContent: {feedback.feedback}\n\nInformation abour sender\n------------------------\nName: {feedback.name}\n E-mail Address: {feedback.email}"
            send_feedback_email(subject, body)
            messages.success(request, f"Thank you for your feedback.")
            return HttpResponseRedirect(reverse('project_search'))
    return render(request, 'feedback.html',{'form':form})


@login_required
@json_view
@require_http_methods(["GET"])
def project_members_list(request, proj_id):
    project = get_object_or_404(Project, pk=proj_id)
    
    if project.user != request.user:
        return JsonResponse({"status": "error", "message": "Project does not belong to you."},
                            status=403, content_type='application/json')
    
    viewers = project.viewers.values_list('email',flat=True)
    return JsonResponse(
        {
            "status": "success", 
            "viewers": list(viewers)
        },
        status=201, content_type='application/json')


@login_required
@json_view
@require_http_methods(["POST"])
def project_share(request, proj_id):
    project = get_object_or_404(Project, pk=proj_id)
    
    if project.user != request.user:
        return JsonResponse({"status": "error", "message": "Project does not belong to you."},
                            status=403, content_type='application/json')
    viewers = CustomUser.objects.filter(email=json.loads(request.body)['userEmail'])
    if viewers.count() > 0 and project.user not in viewers:
        project.viewers.add(viewers.first())
    return JsonResponse(
        {
            "status": "success", 
            "message": "If a user exists with that email address, they will be able to view the project."
        },
        status=201, content_type='application/json')


@login_required
@json_view
@require_http_methods(["POST"])
def project_revoke_access(request, proj_id):
    project = get_object_or_404(Project, pk=proj_id)
    
    if project.user != request.user:
        return JsonResponse({"status": "error", "message": "Project does not belong to you."},
                            status=403, content_type='application/json')
    viewer = CustomUser.objects.filter(email=json.loads(request.body)['userEmail']).first()
    if viewer and project.user != viewer:
        project.viewers.remove(viewer)
        msg = "The selected user will not be able to view the project any more."
        status_code = 204
    else:
        msg = "Could not remove the user from your project. Please contact a moderator."
        status_code = 422
    return JsonResponse(
        {
            "status": "success", 
            "message": msg
        },
        status=status_code, content_type='application/json')


@login_required
@require_http_methods(["GET"])
def project_detail(request, proj_id):
    project = get_object_or_404(Project, pk=proj_id)
    
    if (project.user != request.user) and (request.user not in project.viewers.all()):
        raise PermissionDenied

    logger.info(f"Populating project and economic details in forms.")
    project_form = ProjectDetailForm(None, instance=project)
    economic_data_form = EconomicDataDetailForm(None, instance=project.economic_data)

    return render(request, 'project/project_detail.html',
                  {'project_form': project_form, 'economic_data_form': economic_data_form})


@login_required
@require_http_methods(["GET", "POST"])
def project_create(request):
    if request.POST:
        form = ProjectCreateForm(request.POST)
        if form.is_valid():
            logger.info(f"Creating new project with economic data.")
            economic_data = EconomicData.objects.create(
                duration = form.cleaned_data['duration'],
                currency = form.cleaned_data['currency'],
                discount = form.cleaned_data['discount'],
                tax = form.cleaned_data['tax']
            )

            project = Project.objects.create(
                name = form.cleaned_data['name'],
                description = form.cleaned_data['description'],
                country = form.cleaned_data['country'],
                longitude = form.cleaned_data['longitude'],
                latitude = form.cleaned_data['latitude'],
                user = request.user,
                economic_data = economic_data
            )
            return HttpResponseRedirect(reverse('scenario_search', args=[project.id]))
    else:
        form = ProjectCreateForm()
    return render(request, 'project/project_create.html', {'form': form})


@login_required
@require_http_methods(["GET", "POST"])
def project_update(request, proj_id):
    project = get_object_or_404(Project, pk=proj_id)

    if project.user != request.user:
        raise PermissionDenied
        # return HttpResponseForbidden()

    project_form = ProjectUpdateForm(request.POST or None, instance=project)
    economic_data_form = EconomicDataUpdateForm(request.POST or None, instance=project.economic_data)

    if request.method == "POST" and project_form.is_valid() and economic_data_form.is_valid():
        logger.info(f"Updating project with economic data...")
        project_form.save()
        economic_data_form.save()
        # Save was successful, so send message
        messages.success(request, 'Project Info updated successfully!')
        return HttpResponseRedirect(reverse('project_search'))

    return render(request, 'project/project_update.html',
                  {'project_form': project_form, 'economic_data_form': economic_data_form})


@login_required
@require_http_methods(["POST"])
def project_delete(request, proj_id):
    project = get_object_or_404(Project, pk=proj_id)

    if project.user != request.user:
        raise PermissionDenied

    if request.POST:
        project.delete()
        messages.success(request, 'Project successfully deleted!')

    project_list = Project.objects.filter(user=request.user)
    return render(request, 'project/project_search.html', {'project_list': project_list})


@login_required
@require_http_methods(["GET"])
def project_search(request):
    # project_list = Project.objects.filter(user=request.user)
    # shared_project_list = Project.objects.filter(viewers=request.user)
    combined_projects_list = Project.objects.filter(Q(user=request.user) | Q(viewers=request.user)).distinct()
    return render(request, 'project/project_search.html',
                  {'project_list': combined_projects_list})

# endregion Project


# region Comment

@login_required
@require_http_methods(["GET", "POST"])
def comment_create(request, proj_id):
    project = get_object_or_404(Project, pk=proj_id)

    if request.POST:
        form = CommentForm(request.POST)
        if form.is_valid():
            Comment.objects.create(
                name = form.cleaned_data['name'],
                body = form.cleaned_data['body'],
                project = project
            )
            return HttpResponseRedirect(reverse('scenario_search', args=[proj_id, 1]))

    else: # GET
        form = CommentForm()

    return render(request, 'comment/comment_create.html', {'form': form})


@login_required
@require_http_methods(["GET", "POST"])
def comment_update(request, com_id):
    comment = get_object_or_404(Comment, pk=com_id)

    if comment.project.user != request.user:
        raise PermissionDenied
    
    if request.POST:
        form = CommentForm(request.POST)
        if form.is_valid():
            comment.name = form.cleaned_data['name']
            comment.body = form.cleaned_data['body']
            comment.save()
            return HttpResponseRedirect(reverse('scenario_search', args=[comment.project.id, 1]))
    else: # GET
        form = CommentForm(instance=comment)

    return render(request, 'comment/comment_update.html', {'form': form})


@login_required
@require_http_methods(["POST"])
def comment_delete(request, com_id):
    comment = get_object_or_404(Comment, pk=com_id)

    if comment.project.user != request.user:
        raise PermissionDenied

    if request.POST:
        comment.delete()
        messages.success(request, 'Comment successfully deleted!')
        return HttpResponseRedirect(reverse('scenario_search', args=[comment.project.id, 1]))

# endregion Comment


# region Scenario

@login_required
@require_http_methods(["GET"])
def scenario_search(request, proj_id, show_comments=0):
    """
    This view renders the scenarios and comments search html template.

    args: proj_id, show_comments
    proj_id: The Project id the user requests to observe associated scenarios and comments.
    show_comments: An integer flag to indicate wether the page will open on scenarios tab or comments tab.
    If show_comments==1 the html page will load and following a click event will change the active tab to comments.
    Otherwise the default scenarios tab will be presented to the user.

    Returns: A rendered html template.
    """
    project = get_object_or_404(Project, pk=proj_id)
    return render(request, 'scenario/scenario_search.html',
                  {'comment_list': project.comment_set.all(),
                   'scenarios_list': project.scenario_set.all(),
                   'project': project,
                   'show_comments':show_comments
                   })


@login_required
@require_http_methods(["GET"])
def scenario_create(request, proj_id):
    form = ScenarioCreateForm()
    return render(request, 'scenario/scenario_create.html', {'form': form, 'proj_id':proj_id})


@json_view
@login_required
@require_http_methods(["POST"])
def scenario_create_post(request, proj_id):
    project = get_object_or_404(Project, pk=proj_id)
    form = ScenarioCreateForm(request.POST)

    if form.is_valid():
        scenario = Scenario()
        [setattr(scenario, name, value) for name, value in form.cleaned_data.items()]
        scenario.project = project
        scenario.save()
        return JsonResponse({'success': True}, status=200)
    logger.warning(f"The submitted scenarion has erroneous field values.")
    form_html = crispy_forms_filters.as_crispy_form(form)
    return JsonResponse({'success': False, 'form_html': form_html}, status=422)


@login_required
@require_http_methods(["GET"])
def scenario_view(request, scen_id):
    """ Scenario Update View. GET request only. """
    scenario = get_object_or_404(Scenario, pk=scen_id)

    if (scenario.project.user != request.user) and (request.user not in scenario.project.viewers.all()):
        raise PermissionDenied

    scenario_form = ScenarioUpdateForm(None, instance=scenario)
    return render(request, 'scenario/scenario_info.html', 
        {
            'scenario_form': scenario_form, 
            'scenario': scenario
        })


@login_required
@require_http_methods(["POST"])
def scenario_update(request, scen_id):
    """Scenario Update View. POST request only. """
    scenario = get_object_or_404(Scenario, pk=scen_id)
    if scenario.project.user != request.user:
        raise PermissionDenied
    if request.POST:
        form = ScenarioUpdateForm(request.POST)
        if form.is_valid():
            [setattr(scenario, name, value) for name, value in form.cleaned_data.items()]
            scenario.save(update_fields=form.cleaned_data.keys())
            return HttpResponseRedirect(reverse('scenario_search', args=[scenario.project.id]))
    else:
        raise Http404("An error occurred while updating the Scenario.")


@login_required
@require_http_methods(["GET"])
def scenario_duplicate(request, scen_id):
    """ duplicates the selected scenario and all of its associated components (topology data included) """
    scenario = get_object_or_404(Scenario, pk=scen_id)

    if scenario.project.user != request.user:
        raise PermissionDenied

    # We need to iterate over all the objects related to this scenario and duplicate them
    # and associate them with the new scenario id.
    asset_list = Asset.objects.filter(scenario=scenario)
    bus_list = Bus.objects.filter(scenario=scenario)
    connections_list = ConnectionLink.objects.filter(scenario=scenario)
    # simulation_list = Simulation.objects.filter(scenario=scenario)

    # first duplicate the scenario
    scenario.pk = None
    scenario.save()
    # from now on we are working with the duplicated scenario, not the original
    old2new_asset_ids_map = duplicate_scenario_objects(asset_list, scenario)
    old2new_bus_ids_map = duplicate_scenario_objects(bus_list, scenario, old2new_asset_ids_map)
    duplicate_scenario_connections(connections_list, scenario, old2new_asset_ids_map, old2new_bus_ids_map)
    # duplicate_scenario_objects(simulation_list, scenario)

    return HttpResponseRedirect(reverse('scenario_search', args=[scenario.project.id]))


@login_required
@require_http_methods(["POST"])
def scenario_delete(request, scen_id):
    scenario = get_object_or_404(Scenario, pk=scen_id)
    if scenario.project.user != request.user:
        logger.warning(f"Unauthorized user tried to delete project scenario with db id = {scen_id}.")
        raise PermissionDenied
    if request.POST:
        scenario.delete()
        messages.success(request, 'scenario successfully deleted!')
        return HttpResponseRedirect(reverse('scenario_search', args=[scenario.project.id]))


# class LoadScenarioFromFileView(BSModalCreateView):
#     template_name = 'scenario/load_scenario_from_file.html'
#     form_class = LoadScenarioFromFileForm
#     success_message = 'Success: Scenario Uploaded.'

#     def get_success_url(self):
#         proj_id = self.kwargs['proj_id']
#         return reverse_lazy('scenario_search', args=[proj_id])

# endregion Scenario


# region Asset

@login_required
@require_http_methods(["GET"])
def get_asset_create_form(request, asset_type_name="", asset_uuid=None):
    if asset_type_name == "bus":
        if asset_uuid:
            existing_bus = get_object_or_404(Bus, pk=asset_uuid)
            form = BusForm(asset_type=asset_type_name, instance=existing_bus)
        else:
            form = BusForm(asset_type=asset_type_name)
        return render(request, 'asset/asset_create_form.html', {'form': form})
    elif asset_type_name in ["bess", "h2ess", "gess", "hess"]:
        if asset_uuid:
            existing_ess_asset = get_object_or_404(Asset, unique_id=asset_uuid)
            ess_asset_children = Asset.objects.filter(parent_asset=existing_ess_asset.id)
            ess_capacity_asset = ess_asset_children.get(asset_type__asset_type="capacity")
            ess_charging_power_asset = ess_asset_children.get(asset_type__asset_type="charging_power")
            ess_discharging_power_asset = ess_asset_children.get(asset_type__asset_type="discharging_power")
            # also get all child assets
            form = StorageForm(
                asset_type=asset_type_name, 
                initial={
                'name': existing_ess_asset.name,
                # charging power
                'chp_installed_capacity': ess_charging_power_asset.installed_capacity,
                'chp_age_installed': ess_charging_power_asset.age_installed,
                'chp_capex_fix': ess_charging_power_asset.capex_fix,
                'chp_capex_var': ess_charging_power_asset.capex_var,
                'chp_opex_fix': ess_charging_power_asset.opex_fix,
                'chp_opex_var': ess_charging_power_asset.opex_var,
                'chp_lifetime': ess_charging_power_asset.lifetime,
                'chp_crate': ess_charging_power_asset.crate,
                'chp_efficiency': ess_charging_power_asset.efficiency,
                'chp_dispatchable': ess_charging_power_asset.dispatchable,
                # discharging power
                'dchp_installed_capacity': ess_discharging_power_asset.installed_capacity,
                'dchp_age_installed': ess_discharging_power_asset.age_installed,
                'dchp_capex_fix': ess_discharging_power_asset.capex_fix,
                'dchp_capex_var': ess_discharging_power_asset.capex_var,
                'dchp_opex_fix': ess_discharging_power_asset.opex_fix,
                'dchp_opex_var': ess_discharging_power_asset.opex_var,
                'dchp_lifetime': ess_discharging_power_asset.lifetime,
                'dchp_crate': ess_discharging_power_asset.crate,
                'dchp_efficiency': ess_discharging_power_asset.efficiency,
                'dchp_dispatchable': ess_discharging_power_asset.dispatchable,
                # capacity
                'cp_installed_capacity': ess_capacity_asset.installed_capacity,
                'cp_age_installed': ess_capacity_asset.age_installed,
                'cp_capex_fix': ess_capacity_asset.capex_fix,
                'cp_capex_var': ess_capacity_asset.capex_var,
                'cp_opex_fix': ess_capacity_asset.opex_fix,
                'cp_opex_var': ess_capacity_asset.opex_var,
                'cp_lifetime': ess_capacity_asset.lifetime,
                'cp_crate': ess_capacity_asset.crate,
                'cp_efficiency': ess_capacity_asset.efficiency,
                'cp_dispatchable': ess_capacity_asset.dispatchable,
                'cp_optimize_cap': ess_capacity_asset.optimize_cap,
                'cp_soc_max': ess_capacity_asset.soc_max,
                'cp_soc_min':ess_capacity_asset.soc_min 
                }
            )
        else:
            form = StorageForm(asset_type=asset_type_name)
        return render(request, 'asset/storage_asset_create_form.html', {'form': form})
    else: # all other assets
        if asset_uuid:
            existing_asset = get_object_or_404(Asset, unique_id=asset_uuid)
            form = AssetCreateForm(asset_type=asset_type_name, instance=existing_asset)
            input_timeseries_data=existing_asset.input_timeseries if existing_asset.input_timeseries else ''
        else:
            form = AssetCreateForm(asset_type=asset_type_name)
            input_timeseries_data= ''
        return render(request, 'asset/asset_create_form.html', {'form': form, 'input_timeseries_data':input_timeseries_data})


@login_required
@require_http_methods(["POST"])
def asset_create_or_update(request, scen_id=0, asset_type_name="", asset_uuid=None):
    if asset_type_name == "bus":
        return handle_bus_form_post(request, scen_id, asset_type_name, asset_uuid)
    elif asset_type_name in ["bess", "h2ess", "gess", "hess"]:
        return handle_storage_unit_form_post(request, scen_id, asset_type_name, asset_uuid)
    else: # all assets
        return handle_asset_form_post(request, scen_id, asset_type_name, asset_uuid)


@login_required
@require_http_methods(["GET", "POST"])
def scenario_topology_view(request, scen_id):
    if request.method == "GET":
        scenario = get_object_or_404(Scenario, pk=scen_id)
        topology_data_list = load_scenario_topology_from_db(scen_id)
        return render(request, 'asset/create_asset_topology.html',
            {
                'scenario': scenario, 
                'project_id': scenario.project.id,
                'topology_data_list': json.dumps(topology_data_list)
            })

    elif request.method == "POST" and request.is_ajax():
        scenario = get_object_or_404(Scenario, pk=scen_id)
        if request.user != scenario.project.user:
            raise PermissionDenied
        
        topology = json.loads(request.body)
        node_list = list()
        [node_list.append(NodeObject(topology[idx])) for idx in range(len(topology))]

        # update nodes positioning
        [node.update_asset_coordinates() for node in node_list]

        # delete objects from database which were deleted by the user
        update_deleted_objects_from_database(scen_id, node_list)

        # Make sure there are no connections in the Database to prevent inserting the same connections upon updating.
        ConnectionLink.objects.filter(scenario_id=scen_id).delete()
        for node_obj in node_list:
            create_node_interconnection_links(node_obj, scen_id)
            # node_obj.assign_asset_to_proper_group(node_to_db_mapping_dict)

        return JsonResponse({"success": True}, status=200)
    else:
        return JsonResponse({"success": False, "request": "bad request type. couldn't respond."}, status=400)

# endregion Asset


# region MVS JSON Related

# End-point to send MVS simulation request
@json_view
@login_required
@require_http_methods(["GET", "POST"])
def request_mvs_simulation(request, scenario_id=0):
    if scenario_id == 0:
        return JsonResponse({"status": "error", "error": "No scenario id provided"},
                            status=500, content_type='application/json')
    # Load scenario
    scenario = Scenario.objects.get(pk=scenario_id)
    try:
        data_clean = get_topology_json(scenario)
    except Exception as e:
        logger.error(f"Scenario Serialization ERROR! User: {scenario.project.user.username}. Scenario Id: {scenario.id}. Thrown Exception: {e}.")
        return JsonResponse({"error":f"Scenario Serialization ERROR! Thrown Exception: {e}."},
                        status=500, content_type='application/json')
    
    # delete existing simulation
    Simulation.objects.filter(scenario_id=scenario_id).delete()
    # Create empty Simulation model object
    simulation = Simulation(start_date=datetime.now(), scenario_id=scenario_id)
    # Make simulation request to MVS
    results = mvs_simulation_request(data_clean)

    if results is None:
        return JsonResponse({"status": "error", "error": "Could not communicate with the MVS."},
                            status=407, content_type='application/json')
    
    simulation.mvs_token = results['id'] if results['id'] else None

    if 'status' in results.keys() and (results['status'] == DONE or results['status'] == ERROR):
        simulation.status = results['status']
        simulation.results = results['results']
        simulation.end_date = datetime.now()
    else:  # PENDING
        simulation.status = results['status']
        create_or_delete_simulation_scheduler()

    simulation.elapsed_seconds = (datetime.now() - simulation.start_date).seconds
    simulation.save()

    return JsonResponse({'status': simulation.status,
                         'secondsElapsed': simulation.elapsed_seconds,
                         'rating': simulation.user_rating,
                         "mvs_request_json": data_clean,
                         "mvs_token": simulation.mvs_token
                         },
                        status=200, content_type='application/json')


@json_view
@login_required
@require_http_methods(["POST"])
def update_simulation_rating(request):
    try:
        simulation = Simulation.objects.filter(scenario_id=request.POST['scen_id']).first()
        simulation.user_rating = request.POST['user_rating']
        simulation.save()
        return JsonResponse({'success': True}, status=200, content_type='application/json')
    except Exception as e:
        return JsonResponse({'success': False, 'cause': str(e)}, status=200, content_type='application/json')


@json_view
@login_required
@require_http_methods(["POST"])
def check_simulation_status(request, scen_id):
    try:
        scenario = get_object_or_404(Scenario, pk=scen_id)
        if scenario.simulation:
            return JsonResponse({'success': True, "status": scenario.simulation.status}, status=200, content_type='application/json')
    except Exception as e:
        return JsonResponse({'success': False, 'cause': str(e)}, status=200, content_type='application/json')


# endregion MVS JSON Related
