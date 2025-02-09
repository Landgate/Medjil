document.addEventListener("DOMContentLoaded", function() {
    const fileInput = document.getElementById("fileInput");
    const uploadBtn = document.getElementById("uploadBtn");
    const downloadBtn = document.getElementById("downloadBtn");

    if (uploadBtn && fileInput) {
        uploadBtn.addEventListener("click", function() {
            fileInput.click();
        });

        fileInput.addEventListener("change", function(event) {
            const file = event.target.files[0];
            if (!file) return;
            
            const reader = new FileReader();
            reader.onload = function(e) {
                const data = e.target.result;
                const lines = data.split("\n");
                const formData = {};

                lines.forEach((line) => {
                    const [name, value] = line.split("=");
                    if (name && value) {
                        formData[name.trim()] = value.trim();
                    }
                });

                for (const key in formData) {
                    const input = document.querySelector(`[name="${key}"]`);
                    if (input) {
                        input.value = formData[key];
                    }
                }
            };

            reader.readAsText(file);
        });
    }

    if (downloadBtn) {
        downloadBtn.addEventListener("click", function() {
            const inputs = document.querySelectorAll("input:not([type='file'])[name], select[name]");
            let data = "";

            inputs.forEach(input => {
                data += `${input.name}=${input.value}\n`;
            });

            const blob = new Blob([data], { type: "text/plain" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "form_data.txt";
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        });
    }
});
