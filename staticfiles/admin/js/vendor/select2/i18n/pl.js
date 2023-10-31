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

!function(){if(jQuery&&jQuery.fn&&jQuery.fn.select2&&jQuery.fn.select2.amd)var n=jQuery.fn.select2.amd;n.define("select2/i18n/pl",[],function(){var n=["znak","znaki","znaków"],e=["element","elementy","elementów"],r=function(n,e){return 1===n?e[0]:n>1&&n<=4?e[1]:n>=5?e[2]:void 0};return{errorLoading:function(){return"Nie można załadować wyników."},inputTooLong:function(e){var t=e.input.length-e.maximum;return"Usuń "+t+" "+r(t,n)},inputTooShort:function(e){var t=e.minimum-e.input.length;return"Podaj przynajmniej "+t+" "+r(t,n)},loadingMore:function(){return"Trwa ładowanie…"},maximumSelected:function(n){return"Możesz zaznaczyć tylko "+n.maximum+" "+r(n.maximum,e)},noResults:function(){return"Brak wyników"},searching:function(){return"Trwa wyszukiwanie…"},removeAllItems:function(){return"Usuń wszystkie przedmioty"}}}),n.define,n.require}();