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

!function(){if(jQuery&&jQuery.fn&&jQuery.fn.select2&&jQuery.fn.select2.amd)var n=jQuery.fn.select2.amd;n.define("select2/i18n/bg",[],function(){return{inputTooLong:function(n){var e=n.input.length-n.maximum,u="Моля въведете с "+e+" по-малко символ";return e>1&&(u+="a"),u},inputTooShort:function(n){var e=n.minimum-n.input.length,u="Моля въведете още "+e+" символ";return e>1&&(u+="a"),u},loadingMore:function(){return"Зареждат се още…"},maximumSelected:function(n){var e="Можете да направите до "+n.maximum+" ";return n.maximum>1?e+="избора":e+="избор",e},noResults:function(){return"Няма намерени съвпадения"},searching:function(){return"Търсене…"},removeAllItems:function(){return"Премахнете всички елементи"}}}),n.define,n.require}();