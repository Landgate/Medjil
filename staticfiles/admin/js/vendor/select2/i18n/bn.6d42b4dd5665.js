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

!function(){if(jQuery&&jQuery.fn&&jQuery.fn.select2&&jQuery.fn.select2.amd)var n=jQuery.fn.select2.amd;n.define("select2/i18n/bn",[],function(){return{errorLoading:function(){return"ফলাফলগুলি লোড করা যায়নি।"},inputTooLong:function(n){var e=n.input.length-n.maximum,u="অনুগ্রহ করে "+e+" টি অক্ষর মুছে দিন।";return 1!=e&&(u="অনুগ্রহ করে "+e+" টি অক্ষর মুছে দিন।"),u},inputTooShort:function(n){return n.minimum-n.input.length+" টি অক্ষর অথবা অধিক অক্ষর লিখুন।"},loadingMore:function(){return"আরো ফলাফল লোড হচ্ছে ..."},maximumSelected:function(n){var e=n.maximum+" টি আইটেম নির্বাচন করতে পারবেন।";return 1!=n.maximum&&(e=n.maximum+" টি আইটেম নির্বাচন করতে পারবেন।"),e},noResults:function(){return"কোন ফলাফল পাওয়া যায়নি।"},searching:function(){return"অনুসন্ধান করা হচ্ছে ..."}}}),n.define,n.require}();