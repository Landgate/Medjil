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

!function(){if(jQuery&&jQuery.fn&&jQuery.fn.select2&&jQuery.fn.select2.amd)var n=jQuery.fn.select2.amd;n.define("select2/i18n/he",[],function(){return{errorLoading:function(){return"שגיאה בטעינת התוצאות"},inputTooLong:function(n){var e=n.input.length-n.maximum,r="נא למחוק ";return r+=1===e?"תו אחד":e+" תווים"},inputTooShort:function(n){var e=n.minimum-n.input.length,r="נא להכניס ";return r+=1===e?"תו אחד":e+" תווים",r+=" או יותר"},loadingMore:function(){return"טוען תוצאות נוספות…"},maximumSelected:function(n){var e="באפשרותך לבחור עד ";return 1===n.maximum?e+="פריט אחד":e+=n.maximum+" פריטים",e},noResults:function(){return"לא נמצאו תוצאות"},searching:function(){return"מחפש…"},removeAllItems:function(){return"הסר את כל הפריטים"}}}),n.define,n.require}();