/**
 * Copyright 2024 Code Infinity
 *
 * @author: Chanelle Bösiger <chanelle@codeinfinity.co.za>
 */

/**
 * Function to handle toggling the password field's visibility.
 */
function togglePasswordVisibility() {
    let password = $("#password");

    if (password.attr("type") === "password") {
        password.prop("type", "text");
    } else {
        password.prop("type", "password");
    }
}

/**
 * Function to trim whitespaces from the beginning and end of input fields.
 * @param inputArray
 */
function trimInput(inputArray) {
    if (inputArray.length !== 0) {
        $.each(inputArray, function(index, inputId) {
            const inputField = $("#" + inputId);

            inputField.val(inputField.val().trim());
        });
    }
}

/**
 * Function to handle toggling the active nav links and toggling hidden nav links to show.
 */
function teamQNavSetActive() {
    $(".tq-nav-item").removeClass("active");

    const links = $(".tq-nav-link");

    links.each(function () {
        if (location.pathname.includes("organizations/edit") && this.href.includes("organizations/edit")) {
            $(this).parent().removeClass("d-none")
            $(this).parent().addClass("active");
            $(this).attr("href", location.pathname)
        }

        if (this.href.includes(location.pathname)) {
            $(this).parent().addClass("active");
        }
    });
}

/**
 * Function to redirect a user back to the dashboard.
 * @param progressElement
 */
function getDashboard(progressElement) {
    $(progressElement).show();

    window.location.href = "/player/dashboard";
}

/**
 * Function to handle person attempting to make payment using the "Subscribe Now" button.
 * @param progressElement
 * @param confirmationHash
 * @param element
 * @param redirectLink
 */
function getPayment(progressElement, confirmationHash, element, redirectLink) {
    $(progressElement).show();

    sendRequest(`/player/payment/${confirmationHash}`, null, "GET", function (data) {
        if (data.success) {
            if (data.paid) {
                const message = "Your account has already been settled.";
                const message_type = "danger";

                $(progressElement).hide();
                showMessage(message, message_type, element);

                setTimeout(function () {
                    window.location.reload();
                }, 2000);
            } else {
                $(progressElement).hide();
                window.location.href = redirectLink;
            }
        } else {
            $(progressElement).hide();
            window.location.href = "/login?s_e=1";
        }
    });
}

/**
 * Function to handle preparing the candidate for the assessment and to show an error message if not successful or else
 * to redirect to the assessment.
 * @param progressElement
 * @param confirmationHash
 * @param element
 */
function getAssessment(progressElement, confirmationHash, element) {
    $(progressElement).show();

    sendRequest("/player/assessment/candidate", null, "GET", function (data) {
        if (data === "False") {
            const message = "Error getting assessment. Please try again later.";
            const message_type = "danger";

            $(progressElement).hide();
            showMessage(message, message_type, element);
        } else if (data === "Session") {
            window.location.href="/login?s_e=1";
        } else {
            $(progressElement).hide();
            window.location.href = `/player/assessment/landing/${confirmationHash}`;
        }
    });
}

function getResults(progressElement, assessmentId, confirmationHash, element) {
    $(progressElement).show();

    if (assessmentId && confirmationHash) {
        window.location.href = `/player/assessment/${assessmentId}/results/${confirmationHash}`;
    } else {
        const message = "There was an error processing your results. Please try again later.";
        const message_type = "danger";

        $(progressElement).hide();
        showMessage(message, message_type, element);
    }
}

/**
 * Function to render icons based on a true or false value.
 * @param data
 * @param type
 * @param row
 * @param fieldName
 * @returns {string}
 * @constructor
 */
function CheckOnStatus(data, type, row, fieldName) {
    let icon = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="#E52B50" class="bi bi-x-circle" viewBox="0 0 16 16">
                  <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                  <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
                </svg>`;

    if (row[fieldName] !== 0) {
        icon = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="#00A049" class="bi bi-check-circle" viewBox="0 0 16 16">
                      <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                      <path d="M10.97 4.97a.235.235 0 0 0-.02.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-1.071-1.05z"/>
                </svg>`;
    }

    return icon;
}
