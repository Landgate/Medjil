    
    window.addEventListener('load', function() {
        //Load parent form inputs from Cache if they have been created in a popup
        let inputs = document.querySelectorAll("input:not([type='file'])[name], select[name]");
        let j = inputs.length;
        for (let i = 0; i < j; i++) {
            let el = inputs[i];
            let nameWithIndex = el.attributes["name"].value + "_" + i + "of" + j;
            let cachedVal = sessionStorage.getItem(nameWithIndex)
            if (cachedVal) {
                el.value = cachedVal;
            }
            sessionStorage.removeItem(nameWithIndex);
        }
        
        // Load new_instance to the corresponding input if exists
        let newID = sessionStorage.getItem('new_instance');
        let new_instance_id = sessionStorage.getItem('adding_id');
        new_instance_options = document.querySelector('[id='+ new_instance_id+']');
        
        if (!new_instance_options){
            new_instance_options = document.querySelector('[id$="inst_staff"]');
        }
        if (!new_instance_options){
            new_instance_options = document.querySelector('[id$="inst_level"]');
        }
        if (!new_instance_options){
            new_instance_options = document.querySelector('[id$="_specs"]');
        }
        if (new_instance_options && newID) {
            for(let i = 0; i < new_instance_options.options.length; i++){
                if(new_instance_options.options[i].value == newID){
                    new_instance_options.options[i].selected = true;
                }
            }
            window.sessionStorage.removeItem('new_instance');
            window.sessionStorage.removeItem('new_staff');
            window.sessionStorage.removeItem('new_level');
            window.sessionStorage.removeItem('adding_id');
        }
    });
    
    // cache inputs of parent form and open popup.
    function showAddPopup(triggeringLink) {
        var name = triggeringLink.id.replace(/^add_/, '');
        var inputs, i;
        
        cacheInputs(triggeringLink)
        
        href = triggeringLink.href;
        var win = window.open(href, name, "toolbar=yes,scrollbars=yes,resizable=yes,top=200,left=850,width=700,height=420");
        win.focus();
        return false;
    }
    
    // Cache the inputs on the parent window
    function cacheInputs(triggeringLink){
        
        const trElement = triggeringLink.closest('tr');
        const secondTd = trElement.querySelector('td:nth-child(2)');
        const inputElement = secondTd.querySelector('select');
        if (inputElement){
            window.sessionStorage.setItem('adding_id', inputElement.id);
        }
        
        let inputs = document.querySelectorAll("input:not([type='file'])[name], select[name]");
        let j = inputs.length;
        for (i = 0; i < j; ++i) {
            let el = inputs[i];
            let nameWithIndex = el.attributes["name"].value + "_" + i + "of" + j;
            window.sessionStorage.setItem(nameWithIndex, el.value);
        }
        return false;
    }

    // From parent form, close the popup. (This is called from the view.py)
    function closePopup(win, newID, newRepr) {
        window.sessionStorage.setItem('new_instance',  newID);
        win.close();
    }
    
    //  Refresh Parent Function to load the new item that was added (Called from the popup)
    function refreshParent() {
        window.opener.location.reload(true);
    }