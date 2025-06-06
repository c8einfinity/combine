var formToken = null;

/**
 * Sends an http request
 * @param url
 * @param request
 * @param method
 * @param callback
 */
function sendRequest (url, request, method, callback) {
    if (url === undefined) {
        url = "";
    }
    if (request === undefined) {
        request = null;
    }
    if (method === undefined) {
        method = 'GET';
    }

    const xhr = new XMLHttpRequest();
    xhr.open(method, url, true);

    xhr.onreadystatechange  = function () {
        if (xhr.readyState === 4 && xhr.status === 200) {
            let content = xhr.response;

            try {
                if (xhr.getResponseHeader('FreshToken') !== '' && xhr.getResponseHeader('FreshToken') !== null) {
                    formToken = xhr.getResponseHeader('FreshToken');
                }
            } catch (exception) {
                console.log(exception);
            }

            try {
                content = JSON.parse(content);
                callback(content);
            } catch (exception) {
                callback (content);
            }

        } else if (xhr.status !== 200) {
            let content = xhr.response;
            console.log('An unexpected response occurred while sending request',url, content, xhr.status, xhr.readyState, xhr, xhr.getResponseHeader('Location'));
            callback(xhr.status+" An error occurred, see the console")
        }
    };

    if (method === 'POST') {
        xhr.send(request);
    } else {
        xhr.send(null);
    }
}

/**
 * Gets form data based on a form Id
 * @param formId
 * @returns {FormData}
 */
function getFormData(formId) {
    let data = new FormData();
    let elements = document.querySelectorAll("#" + formId + " select, #" + formId + " input, #" + formId + " textarea");
    for (let ie = 0; ie < elements.length; ie++ )
    {
        let element = elements[ie];
        //refresh the token
        if (element.name === 'formToken' && formToken !== null) {
            element.value = formToken;
        }
        if (element.name) {
            if (element.type === 'file') {
                for (let i = 0; i < element.files.length; i++) {
                    let fileData = element.files[i];
                    let elementName = element.name;
                    if (fileData !== undefined) {
                        if (element.files.length > 1 && !elementName.includes('[')) {
                            elementName = elementName + '[]';
                        }
                        data.append(elementName, fileData, fileData.name);
                    }
                }
            } else if (element.type === 'checkbox' || element.type === 'radio') {
                if (element.checked) {
                    data.append(element.name, element.value)
                } else {
                    if (element.type !== 'radio') {
                        data.append(element.name, "0")
                    }
                }
            } else {
                if (element.value === '') {
                    element.value = null;
                }
                data.append(element.name, element.value);
            }
        }
    }
    return data;
}

/**
 * Handles the data returned from a request
 * @param data
 * @param targetElement
 */
function handleHtmlData(data, targetElement) {
    //Strip out the scripts
    if (data === "") return '';
    const parser = new DOMParser();
    const htmlData = parser.parseFromString(data.includes !== undefined && data.includes('<html>') ? data : '<body>'+data+'</body></html>', 'text/html');
    const body = htmlData.querySelector('body');
    const scripts = body.querySelectorAll('script');
    // remove the script tags
    body.querySelectorAll('script').forEach(script => script.remove());

    if (targetElement !== null) {
        if (body.children.length > 0) {
            document.getElementById(targetElement).replaceChildren(...body.children);
        } else {
            document.getElementById(targetElement).replaceChildren(body.innerHTML);
        }
        if (scripts) {
            scripts.forEach(script => {
                const newScript = document.createElement("script");
                newScript.type = 'text/javascript';
                newScript.async = true;
                newScript.textContent = script.innerText;
                document.getElementById(targetElement).append(newScript);
            });
        }
    } else {
        if (scripts) {
            scripts.forEach(script => {
                const newScript = document.createElement("script");
                newScript.type = 'text/javascript';
                newScript.async = true;
                newScript.textContent = script.innerText;
                document.body.append(newScript);
                console.log(newScript);
            });
        }

        return body.innerHTML;
    }

    return '';
}

/**
 * Loads a page to a target html element
 * @param loadURL
 * @param targetElement
 * @param callback
 * @callback
 */
function loadPage(loadURL, targetElement, callback = null) {
    if (targetElement === undefined) targetElement = 'content';
    sendRequest(loadURL, null, "GET", function(data) {
        let processedHTML = '';
        if (document.getElementById(targetElement) !== null) {
            processedHTML = handleHtmlData(data, targetElement);
        } else {
            if (callback) {
                callback(data);
            } else {
                console.log('TINA4 - define targetElement or callback for loadPage', data);
            }
            return;
        }

        if (callback) {
            callback(processedHTML, data);
        }
    });
}

/**
 * Shows a form from a URL in a target html element
 * @param action
 * @param loadURL
 * @param targetElement
 * @param callback
 */
function showForm(action, loadURL, targetElement, callback = null) {
    if (targetElement === undefined) targetElement = 'form';

    if (action === 'create') action = 'GET';
    if (action === 'edit') action = 'GET';
    if (action === 'delete') action = 'DELETE';

    sendRequest(loadURL, null, action, function(data) {
        let processedHTML = '';
        if (data.message !== undefined) {
            processedHTML = handleHtmlData ((data.message), targetElement);
        } else {
            if (document.getElementById(targetElement) !== null) {
                processedHTML = handleHtmlData (data, targetElement);
            } else {
                if (callback) {
                    callback(data);
                } else {
                    console.log('TINA4 - define targetElement or callback for showForm', data);
                }
                return;
            }
        }

        if (callback) {
            callback(processedHTML);
        }
    });
}

/**
 * Post URL posts data to a specific url
 * @param url
 * @param data
 * @param targetElement
 * @param callback
 */
function postUrl(url, data, targetElement, callback= null) {
    sendRequest(url, data, 'POST', function(data) {
        let processedHTML = '';
        if (data.message !== undefined) {
            processedHTML = handleHtmlData ((data.message), targetElement);
        } else {
            if (document.getElementById(targetElement) !== null) {
                processedHTML =  handleHtmlData (data, targetElement);
            } else {
                if (callback) {
                    callback(data);
                } else {
                    console.log('TINA4 - define targetElement or callback for postUrl', data);
                }
                return;
            }
        }

        if (callback) {
            callback(processedHTML,data)
        }
    });
}


/**
 * Delete URL posts data to a specific url
 * @param url
 * @param data
 * @param targetElement
 * @param callback
 */
function deleteUrl(url, data, targetElement, callback= null) {
    sendRequest(url, data, 'DELETE', function(data) {
        let processedHTML = '';
        if (data.message !== undefined) {
            processedHTML = handleHtmlData ((data.message), targetElement);
        } else {
            if (document.getElementById(targetElement) !== null) {
                processedHTML =  handleHtmlData (data, targetElement);
            } else {
                if (callback) {
                    callback(data);
                } else {
                    console.log('TINA4 - define targetElement or callback for deleteUrl', data);
                }
                return;
            }
        }

        if (callback) {
            callback(processedHTML,data)
        }
    });
}

/**
 * Saves a form to a POST end point
 * @param formId
 * @param targetURL
 * @param targetElement
 * @param callback - optional
 */
function saveForm(formId, targetURL, targetElement, callback = null) {
    if (targetElement === undefined) targetElement = 'message';
    //compile a data model
    let data = getFormData(formId);

    postUrl(targetURL, data, targetElement, callback);
}

/**
 * Alias of saveForm
 * @param formId
 * @param targetURL
 * @param targetElement
 * @param callback
 */
function postForm(formId, targetURL, targetElement, callback = null){
    saveForm(formId, targetURL, targetElement, callback)
}

/**
 * Alias of saveForm
 * @param formId
 * @param targetURL
 * @param targetElement
 * @param callback
 */
function submitForm(formId, targetURL, targetElement, callback = null){
    saveForm(formId, targetURL, targetElement, callback)
}

/**
 * Shows a message
 * @param message
 * @param alertType
 * @param element
 */
function showMessage(message, alertType, element) {
    if (alertType === undefined) {
        alertType = 'info';
    }

    if (!element) {
        element = "message";
    }

    document.getElementById(element).innerHTML = '<div class="alert alert-' + alertType + ' alert-dismissible fade show" role="alert"><strong>Info</strong> ' + message + '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button></div>';

    // Function to close alert after 10 seconds with a slide-up effect.
    $(".alert").delay(10000).slideUp(200, function() {
        $(this).alert('close');
    });
}

/**
 * Set cookie
 * @param name
 * @param value
 * @param days
 */
function setCookie(name, value, days) {
    let expires = "";
    if (days) {
        let date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        expires = "; expires=" + date.toUTCString();
    }
    document.cookie = name + "=" + (value || "") + expires + "; path=/";
}

/**
 * Get cookie
 * @param name
 * @returns {null|string}
 */
function getCookie(name) {
    let nameEQ = name + "=";
    let ca = document.cookie.split(';');
    for (let i = 0; i < ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') c = c.substring(1, c.length);
        if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length, c.length);
    }
    return null;
}

//https://stackoverflow.com/questions/4068373/center-a-popup-window-on-screen
const popupCenter = ({url, title, w, h}) => {
    // Fixes dual-screen position                             Most browsers      Firefox
    const dualScreenLeft = window.screenLeft !== undefined ? window.screenLeft : window.screenX;
    const dualScreenTop = window.screenTop !== undefined ? window.screenTop : window.screenY;

    const width = window.innerWidth ? window.innerWidth : document.documentElement.clientWidth ? document.documentElement.clientWidth : screen.width;
    const height = window.innerHeight ? window.innerHeight : document.documentElement.clientHeight ? document.documentElement.clientHeight : screen.height;

    const systemZoom = width / window.screen.availWidth;
    const left = (width - w) / 2 / systemZoom + dualScreenLeft
    const top = (height - h) / 2 / systemZoom + dualScreenTop
    const newWindow = window.open(url, title,
        `
      directories=no,toolbar=no,location=no,status=no,menubar=no,scrollbars=no,resizable=no,
      width=${w / systemZoom}, 
      height=${h / systemZoom}, 
      top=${top}, 
      left=${left}
      `
    )

    if (window.focus) newWindow.focus();
    return newWindow;
}

/**
 * Opens a popup window
 * @param pdfReportPath
 */
function openReport(pdfReportPath){
    if (pdfReportPath.indexOf("No data available") < 0){
        open(pdfReportPath, "content", "target=_blank, toolbar=no, scrollbars=yes, resizable=yes, width=800, height=600, top=0, left=0");
    }
    else {
        window.alert("Sorry , unable to print a report according to your selection!");
    }
}

/**
 * Does a GET request to an end point
 * @param loadURL
 * @param callback
 */
function getRoute(loadURL, callback) {
    sendRequest(loadURL, null, 'GET', function(data) {
        callback(handleHtmlData (data, null));
    });
}
