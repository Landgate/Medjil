const defaultSiteType = document.querySelector('#id_site_type option[value=""')
defaultSiteType.setAttribute('class', 'default');

const countryInput = document.getElementById('id_country')
const defaultCountryText = document.querySelector('#id_country option[value=""')

if (defaultCountryText) {
    defaultCountryText.setAttribute('class', 'default');
    defaultCountryText.setAttribute('value', '');
}

const stateInput = document.getElementById('id_state')
const defaultStateText = document.querySelector('#id_state option[value=""')

if (defaultStateText) {
    defaultStateText.setAttribute('class', 'default');
    defaultStateText.setAttribute('value', '');
}

const localityInput = document.getElementById('id_locality')
const defaultLocalityText = document.querySelector('#id_locality option[value=""')
if (defaultLocalityText) {
    defaultLocalityText.setAttribute('class', 'default');
    defaultLocalityText.setAttribute('value', '');
}

// var stateOptions = document.getElementById('id_state').options;

countryInput.addEventListener('change', e => {
    
    countryId = e.target.value;    // get the selected country ID from the HTML input
    var url = `get-states-json/${countryId}/` // set the url of the request with the countryid param
    
    // Set option to empty and fill in with default text
    stateInput.innerHTML = '';
    stateInput.appendChild(defaultStateText)
    if (countryId) {
        // Ajax request
        $.ajax({                       // initialize an AJAX request
            type: 'GET',                 // request type
            url: url,                    // set the url of the request (= localhost:8000/hr/ajax/load-cities/)
            data: {
                'country': countryId       // add the country id to the GET parameters
              },
            success: function (response) {   // `respose` is the return of the `load_cities` view function
                // console.log(response.data)
                const stateData = response.data;
                stateData.map(item=> {
                const option = document.createElement('option');
                option.textContent = item.name;
                option.setAttribute('value', item.id)
                stateInput.appendChild(option)
                })
            },
            error: function(error) {
                console.log(error)
            },
        });
    }
});

stateInput.addEventListener('change', e => {
    
    stateId = e.target.value
    console.log(stateId)
    var url = `get-locality-json/${stateId}/`

    // Set option to empty and fill in with default text
    localityInput.innerHTML = '';
    localityInput.appendChild(defaultLocalityText)

    if (stateId) {
        // Ajax Request
        $.ajax({
            type: 'GET',
            url: url,
            success: function(response) {
                console.log(response.data)
                const localityData = response.data;
                localityData.map(item=> {
                const option = document.createElement('option');
                option.textContent = item.name;
                option.setAttribute('value', item.id)
                localityInput.appendChild(option)
                })
            },
            error: function(error) {
                console.log(error)
            },
        })
    }
})