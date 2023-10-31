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

!function(){if(jQuery&&jQuery.fn&&jQuery.fn.select2&&jQuery.fn.select2.amd)var n=jQuery.fn.select2.amd;n.define("select2/i18n/lt",[],function(){function n(n,e,i,t){return n%10==1&&(n%100<11||n%100>19)?e:n%10>=2&&n%10<=9&&(n%100<11||n%100>19)?i:t}return{inputTooLong:function(e){var i=e.input.length-e.maximum,t="Pašalinkite "+i+" simbol";return t+=n(i,"į","ius","ių")},inputTooShort:function(e){var i=e.minimum-e.input.length,t="Įrašykite dar "+i+" simbol";return t+=n(i,"į","ius","ių")},loadingMore:function(){return"Kraunama daugiau rezultatų…"},maximumSelected:function(e){var i="Jūs galite pasirinkti tik "+e.maximum+" element";return i+=n(e.maximum,"ą","us","ų")},noResults:function(){return"Atitikmenų nerasta"},searching:function(){return"Ieškoma…"},removeAllItems:function(){return"Pašalinti visus elementus"}}}),n.define,n.require}();