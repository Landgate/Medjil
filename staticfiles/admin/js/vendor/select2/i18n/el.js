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

!function(){if(jQuery&&jQuery.fn&&jQuery.fn.select2&&jQuery.fn.select2.amd)var n=jQuery.fn.select2.amd;n.define("select2/i18n/el",[],function(){return{errorLoading:function(){return"Τα αποτελέσματα δεν μπόρεσαν να φορτώσουν."},inputTooLong:function(n){var e=n.input.length-n.maximum,u="Παρακαλώ διαγράψτε "+e+" χαρακτήρ";return 1==e&&(u+="α"),1!=e&&(u+="ες"),u},inputTooShort:function(n){return"Παρακαλώ συμπληρώστε "+(n.minimum-n.input.length)+" ή περισσότερους χαρακτήρες"},loadingMore:function(){return"Φόρτωση περισσότερων αποτελεσμάτων…"},maximumSelected:function(n){var e="Μπορείτε να επιλέξετε μόνο "+n.maximum+" επιλογ";return 1==n.maximum&&(e+="ή"),1!=n.maximum&&(e+="ές"),e},noResults:function(){return"Δεν βρέθηκαν αποτελέσματα"},searching:function(){return"Αναζήτηση…"},removeAllItems:function(){return"Καταργήστε όλα τα στοιχεία"}}}),n.define,n.require}();