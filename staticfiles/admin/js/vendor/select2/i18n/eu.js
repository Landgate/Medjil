/*

   © 2023 Western Australian Land Information Authority

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
/*! Select2 4.0.13 | https://github.com/select2/select2/blob/master/LICENSE.md */

!function(){if(jQuery&&jQuery.fn&&jQuery.fn.select2&&jQuery.fn.select2.amd)var e=jQuery.fn.select2.amd;e.define("select2/i18n/eu",[],function(){return{inputTooLong:function(e){var t=e.input.length-e.maximum,n="Idatzi ";return n+=1==t?"karaktere bat":t+" karaktere",n+=" gutxiago"},inputTooShort:function(e){var t=e.minimum-e.input.length,n="Idatzi ";return n+=1==t?"karaktere bat":t+" karaktere",n+=" gehiago"},loadingMore:function(){return"Emaitza gehiago kargatzen…"},maximumSelected:function(e){return 1===e.maximum?"Elementu bakarra hauta dezakezu":e.maximum+" elementu hauta ditzakezu soilik"},noResults:function(){return"Ez da bat datorrenik aurkitu"},searching:function(){return"Bilatzen…"},removeAllItems:function(){return"Kendu elementu guztiak"}}}),e.define,e.require}();