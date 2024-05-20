/*

   © 2024 Western Australian Land Information Authority

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

*/
    window.addEventListener('load', function() {
        var makes_dataList = document.getElementById('makes');
        
        if (makes_dataList){
            db_makes.forEach(function(item) {
                var option = document.createElement('option');
                option.value = item.make;
                makes_dataList.appendChild(option);
            });
            filter_models();
        }
    });
    
    function filter_models(){
        make_input = document.querySelector('[id$="_make_name"]').value.toUpperCase();
        var models_dataList = document.getElementById('models');
        models_dataList.innerHTML = '';
        
        if (make_input){
            var make_object = db_makes.find(function(record){
                return record.make === make_input;
            });
        }
        if (make_object){
            db_models.forEach(function(item) {
            if (make_object.id === item.make_id){
                var option = document.createElement('option');
                option.value = item.model;
                models_dataList.appendChild(option);
            }
            });
        }
    }
    