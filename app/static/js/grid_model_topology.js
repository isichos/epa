"use strict";var _this3=void 0;function _createForOfIteratorHelper(a,b){var c="undefined"!=typeof Symbol&&a[Symbol.iterator]||a["@@iterator"];if(!c){if(Array.isArray(a)||(c=_unsupportedIterableToArray(a))||b&&a&&"number"==typeof a.length){c&&(a=c);var d=0,e=function(){};return{s:e,n:function(){return d>=a.length?{done:!0}:{done:!1,value:a[d++]}},e:function(a){throw a},f:e}}throw new TypeError("Invalid attempt to iterate non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.")}var f,g=!0,h=!1;return{s:function(){c=c.call(a)},n:function(){var a=c.next();return g=a.done,a},e:function(a){h=!0,f=a},f:function(){try{g||null==c.return||c.return()}finally{if(h)throw f}}}}function _unsupportedIterableToArray(a,b){if(a){if("string"==typeof a)return _arrayLikeToArray(a,b);var c=Object.prototype.toString.call(a).slice(8,-1);return"Object"===c&&a.constructor&&(c=a.constructor.name),"Map"===c||"Set"===c?Array.from(a):"Arguments"===c||/^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(c)?_arrayLikeToArray(a,b):void 0}}function _arrayLikeToArray(a,b){(null==b||b>a.length)&&(b=a.length);for(var c=0,d=Array(b);c<b;c++)d[c]=a[c];return d}function _newArrowCheck(a,b){if(a!==b)throw new TypeError("Cannot instantiate an arrow function")}// Constants
const ASSET_TYPE_NAME="asset_type_name",BUS="bus",nodesToDB=new Map,id=document.getElementById("drawflow"),editor=new Drawflow(id);editor.reroute=!0,editor.start();// editor.drawflow.drawflow.Home.data; // All node level data are saved here
/* Mouse and Touch Actions */var elements=document.getElementsByClassName("drag-drawflow");for(let a=0;a<elements.length;a++)elements[a].addEventListener("touchend",drop,!1),elements[a].addEventListener("touchstart",drag,!1);function allowDrop(a){a.preventDefault()}function drag(a){a.dataTransfer.setData("node",a.target.getAttribute("data-node"))}function drop(a){a.preventDefault();const b=a.dataTransfer.getData("node");b===BUS?IOBusOptions(b,a.clientX,a.clientY):addNodeToDrawFlow(b,a.clientX,a.clientY)}function IOBusOptions(a,b,c){var d=this;const e=function(a,b,c){return _newArrowCheck(this,d),a<=b?b:a>=c?c:a}.bind(this);Swal.mixin({input:"number",confirmButtonText:"Next",showCancelButton:!0,progressSteps:["1","2"]}).queue([{title:"Bus Inputs",text:"Provide the number of bus Inputs (default 1)"},{title:"Bus Outputs",text:"Provide the number of bus Outputs (default 1)"}]).then(function(f){if(_newArrowCheck(this,d),f.value){const d=e(f.value[0],1,7),g=e(f.value[1],1,7);addNodeToDrawFlow(a,b,c,d,g)}}.bind(this))}// Disallow Any Connection to be created without a bus.
editor.on("connectionCreated",function(a){var b=editor.getNodeFromId(a.input_id),c=editor.getNodeFromId(a.output_id);(b.name!==BUS&&c.name!==BUS||b.name===BUS&&c.name===BUS)&&(editor.removeSingleConnection(a.output_id,a.input_id,a.output_class,a.input_class),Swal.fire("Unexpected Connection","Please connect assets to each other\n only through a bus node. Interconnecting busses is also not allowed.","error"))}),editor.on("nodeCreated",function(){// region bind installed_capacity to age_installed Changes
// const nodeIdInstalledCapInput = document.getElementById(`node-${nodeID}`).querySelector("input[name='installed_capacity']");
// if (nodeIdInstalledCapInput) {
//     nodeIdInstalledCapInput.addEventListener('change', function (e) {
//         const ageInstalledElement = e.target.closest("#FormGroup").querySelector("input[name='age_installed']");
//         if (e.target.value === '0') {
//             ageInstalledElement.value = '0';
//             ageInstalledElement.readOnly = true;
//             let notifyAgeInputEvent = new Event("input", { bubbles: true });
//             ageInstalledElement.dispatchEvent(notifyAgeInputEvent);
//         } else
//             ageInstalledElement.readOnly = false;
//     });
//     // for existing nodes check if installed cap is zero and set age_installed to read only
//     if (nodeIdInstalledCapInput.value === '0')
//         nodeIdInstalledCapInput.closest("#FormGroup").querySelector("input[name='age_installed']").readOnly = true;
// }
// endregion
}),editor.on("nodeRemoved",function(a){// remove nodeID from nodesToDB
nodesToDB.delete("node-"+a)});async function addNodeToDrawFlow(a,b,c,d=1,e=1,f={}){return"fixed"!==editor.editor_mode&&(b=b*(editor.precanvas.clientWidth/(editor.precanvas.clientWidth*editor.zoom))-editor.precanvas.getBoundingClientRect().x*(editor.precanvas.clientWidth/(editor.precanvas.clientWidth*editor.zoom)),c=c*(editor.precanvas.clientHeight/(editor.precanvas.clientHeight*editor.zoom))-editor.precanvas.getBoundingClientRect().y*(editor.precanvas.clientHeight/(editor.precanvas.clientHeight*editor.zoom)),createNodeObject(a,d,e,{},b,c));// the following translation/transformation is required to correctly drop the nodes in the current clientScreen
}// region Show Modal either by double clicking the box or the drawflow node.
var transform="";document.addEventListener("dblclick",function(a){var b=this;const c=function(a){a.closest(".drawflow-node").style.zIndex="9999",a.querySelector(".modal").style.display="block",transform=editor.precanvas.style.transform,editor.precanvas.style.transform="",editor.precanvas.style.left=editor.canvas_x+"px",editor.precanvas.style.top=editor.canvas_y+"px",editor.editor_mode="fixed"},d=a.target.closest(".drawflow-node"),e=d.querySelector(".box").getAttribute(ASSET_TYPE_NAME);if(d&&"block"!==d.querySelector(".modal").style.display){const a=d.id,f=formGetUrl+e+(nodesToDB.has(a)?"/"+nodesToDB.get(a).uid:"");fetch(f).then(function(a){return _newArrowCheck(this,b),a.text()}.bind(this)).then(function(a){_newArrowCheck(this,b);const e=d.querySelector("form").parentNode;// console.log(formParentDiv);
e.innerHTML=a;const f=e.closest(".box");c(f)}.bind(this)).catch(function(a){return _newArrowCheck(this,b),console.log("Modal get form JS Error: "+a)}.bind(this))}});// endregion
// region close Modal on: 1. click 'x', 2. press 'esc' and 3. click outside the modal.
function closeModalSteps(a){// // Change the name of the node based on input
const b=a.closest(".drawflow_content_node").querySelector(".nodeName");// End name change
// hide the modal
// bring node to default z-index
// delete modal form
b.textContent=`${a.querySelector("input[df-name]").value}`,a.style.display="none",a.closest(".drawflow-node").style.zIndex=a.closest(".drawflow-node").classList.contains("ess")?"1":"2",editor.precanvas.style.transform=transform,editor.precanvas.style.left="0px",editor.precanvas.style.top="0px",editor.editor_mode="edit",a.querySelector("form").parentNode.innerHTML="<form></form>"}const closemodal=function(a){return _newArrowCheck(this,_this3),closeModalSteps(a.target.closest(".modal"))}.bind(void 0),submitForm=function(a){var b=this;_newArrowCheck(this,_this3);const c=a.target.closest(".modal-content").querySelector("form"),d=c.closest(".box").getAttribute(ASSET_TYPE_NAME),e=c.closest(".drawflow-node").id,f=e.split("-").pop(),g=formPostUrl+d+(nodesToDB.has(e)?"/"+nodesToDB.get(e).uid:""),h=new FormData(c),i=editor.drawflow.drawflow.Home.data[f].pos_x,j=editor.drawflow.drawflow.Home.data[f].pos_y;if(h.set("pos_x",i),h.set("pos_y",j),d===BUS){const a=Object.keys(editor.drawflow.drawflow.Home.data[f].inputs).length,b=Object.keys(editor.drawflow.drawflow.Home.data[f].outputs).length;h.set("input_ports",a),h.set("output_ports",b)}fetch(g,{method:"POST",headers:{// 'Content-Type': 'multipart/form-data', //'application/json', // if enabled then read json.loads(request.body) in the backend
"X-CSRFToken":csrfToken},body:h}).then(function(a){return _newArrowCheck(this,b),a.json()}.bind(this)).then(function(f){_newArrowCheck(this,b),f.success?(!1===nodesToDB.has(e)&&nodesToDB.set(e,{uid:f.asset_id,assetTypeName:d}),closeModalSteps(a.target.closest(".modal"))):c.innerHTML=f.form_html}.bind(this)).catch(function(a){return _newArrowCheck(this,b),console.log("Modal form JS Error: "+a)}.bind(this))}.bind(void 0);document.addEventListener("keydown",function(a){const b=document.getElementsByClassName("modal");if(27===a.keyCode){var c,d=_createForOfIteratorHelper(b);try{for(d.s();!(c=d.n()).done;){let a=c.value;"block"===a.style.display&&closeModalSteps(a)}}catch(a){d.e(a)}finally{d.f()}}}),window.onclick=function(a){const b=document.getElementsByClassName("modal");var c,d=_createForOfIteratorHelper(b);try{for(d.s();!(c=d.n()).done;){const b=c.value;a.target===b&&"block"===b.style.display&&closeModalSteps(b)}}catch(a){d.e(a)}finally{d.f()}};// endregion set
async function createNodeObject(a,b=1,c=1,d={},e,f){const g="undefined"==typeof d.name?a:d.name,h=`<div class="box" ${ASSET_TYPE_NAME}="${a}">
        <div class="modal" style="display:none">
          <div class="modal-content">
            <span class="close" onclick="closemodal(event)">&times;</span>
            <br>
            <h2 class="panel-heading" text-align: left">${a.replaceAll("_"," ")} Properties</h2>
            <br>
            <div class="row">
            <div class="col-md-1"></div>
            <div class="col-md-10">
                <form></form>
            </div>
            </div>
            <br>
            <div class="row">
                <div class="col-md-3"></div>
                <div class="col-md-6">
                ${scenarioBelongsToUser?"<button class=\"modalbutton\" style=\"font-size: medium; font-family: century gothic\" onclick=\"submitForm(event)\">Ok</button>":""}
                </div>
            </div>
          </div>
        </div>
    </div>
    <div class="nodeName" >${g}</div>`;return{editorNodeId:editor.addNode(a,b,c,e,f,a,d,h),specificNodeType:a}}