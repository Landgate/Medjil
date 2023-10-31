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

!function(){if(jQuery&&jQuery.fn&&jQuery.fn.select2&&jQuery.fn.select2.amd)var n=jQuery.fn.select2.amd;n.define("select2/i18n/sr-Cyrl",[],function(){function n(n,e,r,u){return n%10==1&&n%100!=11?e:n%10>=2&&n%10<=4&&(n%100<12||n%100>14)?r:u}return{errorLoading:function(){return"Преузимање није успело."},inputTooLong:function(e){var r=e.input.length-e.maximum,u="Обришите "+r+" симбол";return u+=n(r,"","а","а")},inputTooShort:function(e){var r=e.minimum-e.input.length,u="Укуцајте бар још "+r+" симбол";return u+=n(r,"","а","а")},loadingMore:function(){return"Преузимање још резултата…"},maximumSelected:function(e){var r="Можете изабрати само "+e.maximum+" ставк";return r+=n(e.maximum,"у","е","и")},noResults:function(){return"Ништа није пронађено"},searching:function(){return"Претрага…"},removeAllItems:function(){return"Уклоните све ставке"}}}),n.define,n.require}();