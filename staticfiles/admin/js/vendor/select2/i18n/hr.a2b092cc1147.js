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

!function(){if(jQuery&&jQuery.fn&&jQuery.fn.select2&&jQuery.fn.select2.amd)var n=jQuery.fn.select2.amd;n.define("select2/i18n/hr",[],function(){function n(n){var e=" "+n+" znak";return n%10<5&&n%10>0&&(n%100<5||n%100>19)?n%10>1&&(e+="a"):e+="ova",e}return{errorLoading:function(){return"Preuzimanje nije uspjelo."},inputTooLong:function(e){return"Unesite "+n(e.input.length-e.maximum)},inputTooShort:function(e){return"Unesite još "+n(e.minimum-e.input.length)},loadingMore:function(){return"Učitavanje rezultata…"},maximumSelected:function(n){return"Maksimalan broj odabranih stavki je "+n.maximum},noResults:function(){return"Nema rezultata"},searching:function(){return"Pretraga…"},removeAllItems:function(){return"Ukloni sve stavke"}}}),n.define,n.require}();