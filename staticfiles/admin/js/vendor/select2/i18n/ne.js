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

!function(){if(jQuery&&jQuery.fn&&jQuery.fn.select2&&jQuery.fn.select2.amd)var n=jQuery.fn.select2.amd;n.define("select2/i18n/ne",[],function(){return{errorLoading:function(){return"नतिजाहरु देखाउन सकिएन।"},inputTooLong:function(n){var e=n.input.length-n.maximum,u="कृपया "+e+" अक्षर मेटाउनुहोस्।";return 1!=e&&(u+="कृपया "+e+" अक्षरहरु मेटाउनुहोस्।"),u},inputTooShort:function(n){return"कृपया बाँकी रहेका "+(n.minimum-n.input.length)+" वा अरु धेरै अक्षरहरु भर्नुहोस्।"},loadingMore:function(){return"अरु नतिजाहरु भरिँदैछन् …"},maximumSelected:function(n){var e="तँपाई "+n.maximum+" वस्तु मात्र छान्न पाउँनुहुन्छ।";return 1!=n.maximum&&(e="तँपाई "+n.maximum+" वस्तुहरु मात्र छान्न पाउँनुहुन्छ।"),e},noResults:function(){return"कुनै पनि नतिजा भेटिएन।"},searching:function(){return"खोजि हुँदैछ…"}}}),n.define,n.require}();