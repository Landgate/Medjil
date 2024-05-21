    //Load parent form inputs from Cache if they have been created in a popup
    window.addEventListener('load', function() {
        let inputs = document.querySelectorAll("input,select");
        for (let i = 0; i < inputs.length; i++) {
            let el = inputs[i];
            let cachedVal = sessionStorage.getItem(el.attributes["name"].value)
            if (cachedVal) {
                el.value = cachedVal;
            }
            sessionStorage.removeItem(el.attributes["name"].value);
        }
        let newID = sessionStorage.getItem('new_instance');
        let new_instance_options = document.querySelector('[id$="inst_staff"]');
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
        }
    });
    
    // cache inputs of parent form and open popup.
    function showAddPopup(triggeringLink) {
        var name = triggeringLink.id.replace(/^add_/, '');
        var inputs, i;
        
        // Cache the inputs on the parent window
        inputs = document.querySelectorAll("input,select");
        for (i = 0; i < inputs.length; ++i) {
            let el = inputs[i];
            window.sessionStorage.setItem(el.attributes["name"].value, el.value);
        }
        
        href = triggeringLink.href;
        var win = window.open(href, name, "toolbar=yes,scrollbars=yes,resizable=yes,top=200,left=850,width=700,height=420");
        win.focus();
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