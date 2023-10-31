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
/**
 * Persist changelist filters state (collapsed/expanded).
 */
'use strict';
{
    // Init filters.
    let filters = JSON.parse(sessionStorage.getItem('django.admin.filtersState'));

    if (!filters) {
        filters = {};
    }

    Object.entries(filters).forEach(([key, value]) => {
        const detailElement = document.querySelector(`[data-filter-title='${key}']`);

        // Check if the filter is present, it could be from other view.
        if (detailElement) {
            value ? detailElement.setAttribute('open', '') : detailElement.removeAttribute('open');
        }
    });

    // Save filter state when clicks.
    const details = document.querySelectorAll('details');
    details.forEach(detail => {
        detail.addEventListener('toggle', event => {
            filters[`${event.target.dataset.filterTitle}`] = detail.open;
            sessionStorage.setItem('django.admin.filtersState', JSON.stringify(filters));
        });
    });
}
