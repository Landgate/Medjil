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

!function(){if(jQuery&&jQuery.fn&&jQuery.fn.select2&&jQuery.fn.select2.amd)var n=jQuery.fn.select2.amd;n.define("select2/i18n/dsb",[],function(){var n=["znamuško","znamušce","znamuška","znamuškow"],e=["zapisk","zapiska","zapiski","zapiskow"],u=function(n,e){return 1===n?e[0]:2===n?e[1]:n>2&&n<=4?e[2]:n>=5?e[3]:void 0};return{errorLoading:function(){return"Wuslědki njejsu se dali zacytaś."},inputTooLong:function(e){var a=e.input.length-e.maximum;return"Pšosym lašuj "+a+" "+u(a,n)},inputTooShort:function(e){var a=e.minimum-e.input.length;return"Pšosym zapódaj nanejmjenjej "+a+" "+u(a,n)},loadingMore:function(){return"Dalšne wuslědki se zacytaju…"},maximumSelected:function(n){return"Móžoš jano "+n.maximum+" "+u(n.maximum,e)+"wubraś."},noResults:function(){return"Žedne wuslědki namakane"},searching:function(){return"Pyta se…"},removeAllItems:function(){return"Remove all items"}}}),n.define,n.require}();