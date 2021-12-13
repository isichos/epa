from django.urls import path, re_path
from .views import *

urlpatterns = [
    path('', project_search, name='home'),
    # Project
    path('project/create/', project_create, name='project_create'),
    path('project/search/', project_search, name='project_search'),
    path('project/update/<int:proj_id>', project_update, name='project_update'),
    path('project/detail/<int:proj_id>', project_detail, name='project_detail'),
    path('project/delete/<int:proj_id>', project_delete, name='project_delete'),
    path('project/project_members_list/<int:proj_id>', project_members_list, name='project_members_list'),
    path('project/share/<int:proj_id>', project_share, name='project_share'),
    path('project/unshare/<int:proj_id>', project_revoke_access, name='project_revoke_access'),
    # Comment
    path('comment/create/<int:proj_id>', comment_create, name='comment_create'),
    path('comment/update/<int:com_id>', comment_update, name='comment_update'),
    path('comment/delete/<int:com_id>', comment_delete, name='comment_delete'),
    # Scenario
    path('scenario/search/<int:proj_id>', scenario_search, name='scenario_search'),
    path('scenario/search/<int:proj_id>/<int:show_comments>', scenario_search, name='scenario_search'),
    path('scenario/create/<int:proj_id>', scenario_create, name='scenario_create'),
    path('scenario/create_post/<int:proj_id>', scenario_create_post, name='scenario_create_post'),
    path('scenario/update/<int:scen_id>', scenario_update, name='scenario_update'),
    path('scenario/delete/<int:scen_id>', scenario_delete, name='scenario_delete'),
    path('scenario/view/<int:scen_id>', scenario_view, name='scenario_view'),
    path('scenario/duplicate/<int:scen_id>', scenario_duplicate, name='scenario_duplicate'),
    # path('scenario/upload/<int:proj_id>', LoadScenarioFromFileView.as_view(), name='scenario_upload'),
    # Grid Model (Assets Creation)
    path('asset/assets_topology/<int:scen_id>', scenario_topology_view, name='new_assets_topology'),
    re_path(r'^asset/get_form/(?P<asset_type_name>\w+)?(/(?P<asset_uuid>[0-9a-f-]+))?$', get_asset_create_form, name='get_asset_create_form'),
    re_path(r'^asset/create_or_update_post/(?P<scen_id>\d+)/(?P<asset_type_name>\w+)?(/(?P<asset_uuid>[0-9a-f-]+))?$', asset_create_or_update, name='asset_create_or_update'),
    # MVS Simulation
    path('topology/mvs_simulation/<int:scenario_id>', request_mvs_simulation, name='request_mvs_simulation'),
    path('topology/update_simulation_rating/', update_simulation_rating, name='update_simulation_rating'),
    # path('topology/simulation_status/<int:scen_id>', check_simulation_status, name='check_simulation_status'),
    re_path(r'^topology/simulation_status/(?P<scen_id>\d+)?$', check_simulation_status, name='check_simulation_status'),
    # User Feedback
    path('user_feedback', user_feedback, name='user_feedback'),
   
]
