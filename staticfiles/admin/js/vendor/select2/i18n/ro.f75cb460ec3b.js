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

!function(){if(jQuery&&jQuery.fn&&jQuery.fn.select2&&jQuery.fn.select2.amd)var e=jQuery.fn.select2.amd;e.define("select2/i18n/ro",[],function(){return{errorLoading:function(){return"Rezultatele nu au putut fi incărcate."},inputTooLong:function(e){var t=e.input.length-e.maximum,n="Vă rugăm să ștergeți"+t+" caracter";return 1!==t&&(n+="e"),n},inputTooShort:function(e){return"Vă rugăm să introduceți "+(e.minimum-e.input.length)+" sau mai multe caractere"},loadingMore:function(){return"Se încarcă mai multe rezultate…"},maximumSelected:function(e){var t="Aveți voie să selectați cel mult "+e.maximum;return t+=" element",1!==e.maximum&&(t+="e"),t},noResults:function(){return"Nu au fost găsite rezultate"},searching:function(){return"Căutare…"},removeAllItems:function(){return"Eliminați toate elementele"}}}),e.define,e.require}();