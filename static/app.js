/* Patient Data Entry — validate the form, submit it, render the list.
   All user-supplied text reaches the DOM via textContent only. */

(function () {
  "use strict";

  var GENDERS = ["Female", "Male", "Other", "Prefer not to say"];
  var MIN_PHONE_DIGITS = 7;
  var EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
  var DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
  var PHONE_RE = /^\+?[0-9 ().\-]+$/;

  var form = document.getElementById("patient-form");
  var formError = document.getElementById("form-error");
  var formNote = document.getElementById("form-note");
  var patientsList = document.getElementById("patients-list");
  var patientsCount = document.getElementById("patients-count");
  var dobInput = document.getElementById("pat-dob");

  function show(el, msg) {
    el.textContent = msg;
    el.hidden = false;
  }

  function hide(el) {
    el.hidden = true;
    el.textContent = "";
  }

  function api(path, options) {
    return fetch(path, options).then(function (res) {
      return res.json().then(function (data) {
        if (!res.ok) {
          throw new Error(data.error || "Something went wrong.");
        }
        return data;
      });
    });
  }

  function postJSON(path, payload) {
    return api(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  }

  function todayISO() {
    var now = new Date();
    var month = String(now.getMonth() + 1);
    var day = String(now.getDate());
    return now.getFullYear() + "-" +
      (month.length < 2 ? "0" : "") + month + "-" +
      (day.length < 2 ? "0" : "") + day;
  }

  function isRealDate(iso) {
    if (!DATE_RE.test(iso)) {
      return false;
    }
    var d = new Date(iso + "T00:00:00");
    return !isNaN(d.getTime()) &&
      d.getFullYear() === Number(iso.slice(0, 4)) &&
      d.getMonth() === Number(iso.slice(5, 7)) - 1 &&
      d.getDate() === Number(iso.slice(8, 10));
  }

  function digitCount(value) {
    var count = 0;
    for (var i = 0; i < value.length; i++) {
      if (value[i] >= "0" && value[i] <= "9") {
        count++;
      }
    }
    return count;
  }

  function isPhone(value) {
    return PHONE_RE.test(value) && digitCount(value) >= MIN_PHONE_DIGITS;
  }

  /* Returns a field-name -> message map; empty means the payload is valid. */
  function validate(payload) {
    var errors = {};
    if (!payload.first_name) {
      errors.first_name = "First name is required.";
    }
    if (!payload.last_name) {
      errors.last_name = "Last name is required.";
    }
    if (!payload.date_of_birth) {
      errors.date_of_birth = "Date of birth is required.";
    } else if (!isRealDate(payload.date_of_birth)) {
      errors.date_of_birth = "A valid date of birth is required.";
    } else if (payload.date_of_birth > todayISO()) {
      errors.date_of_birth = "Date of birth cannot be in the future.";
    }
    if (GENDERS.indexOf(payload.gender) === -1) {
      errors.gender = "Please choose a gender from the list.";
    }
    if (!payload.phone) {
      errors.phone = "Phone number is required.";
    } else if (!isPhone(payload.phone)) {
      errors.phone = "A valid phone number is required.";
    }
    if (payload.email && !EMAIL_RE.test(payload.email)) {
      errors.email = "A valid email address is required.";
    }
    if (payload.emergency_contact_phone &&
        !isPhone(payload.emergency_contact_phone)) {
      errors.emergency_contact_phone =
        "A valid emergency contact phone is required.";
    }
    return errors;
  }

  function clearFieldErrors() {
    var marked = form.querySelectorAll(".invalid");
    for (var i = 0; i < marked.length; i++) {
      marked[i].classList.remove("invalid");
    }
    var messages = form.querySelectorAll(".field-error");
    for (var j = 0; j < messages.length; j++) {
      hide(messages[j]);
    }
  }

  function markFieldError(name, message) {
    var input = form.querySelector('[name="' + name + '"]');
    var messageEl = form.querySelector(
      '.field-error[data-field="' + name + '"]');
    if (input) {
      input.classList.add("invalid");
    }
    if (messageEl) {
      show(messageEl, message);
    }
  }

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    hide(formError);
    hide(formNote);
    clearFieldErrors();
    var payload = {
      first_name: document.getElementById("pat-first-name").value.trim(),
      last_name: document.getElementById("pat-last-name").value.trim(),
      date_of_birth: dobInput.value,
      gender: document.getElementById("pat-gender").value,
      phone: document.getElementById("pat-phone").value.trim(),
      email: document.getElementById("pat-email").value.trim(),
      street_address: document.getElementById("pat-street").value.trim(),
      city: document.getElementById("pat-city").value.trim(),
      state_region: document.getElementById("pat-state").value.trim(),
      postal_code: document.getElementById("pat-postal").value.trim(),
      emergency_contact_name:
        document.getElementById("pat-ec-name").value.trim(),
      emergency_contact_phone:
        document.getElementById("pat-ec-phone").value.trim(),
      notes: document.getElementById("pat-notes").value.trim(),
    };
    var errors = validate(payload);
    var names = Object.keys(errors);
    if (names.length > 0) {
      names.forEach(function (name) {
        markFieldError(name, errors[name]);
      });
      var first = form.querySelector('[name="' + names[0] + '"]');
      if (first) {
        first.focus();
      }
      return;
    }
    var button = form.querySelector("button");
    button.disabled = true;
    postJSON("/api/patients", payload)
      .then(function () {
        form.reset();
        document.getElementById("pat-gender").selectedIndex = 0;
        show(formNote, "Patient saved.");
        loadPatients();
      })
      .catch(function (err) {
        show(formError, err.message);
      })
      .finally(function () {
        button.disabled = false;
      });
  });

  function formatDate(iso) {
    var d = new Date(iso + "T00:00:00");
    if (isNaN(d.getTime())) {
      return iso;
    }
    return d.toLocaleDateString("en-GB", {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  }

  function renderPatients(patients) {
    while (patientsList.firstChild) {
      patientsList.removeChild(patientsList.firstChild);
    }
    if (patients.length === 0) {
      var empty = document.createElement("p");
      empty.className = "list-empty";
      empty.textContent =
        "No patients entered yet — submit the form above to add the first.";
      patientsList.appendChild(empty);
      return;
    }
    patients.forEach(function (pat) {
      var card = document.createElement("article");
      card.className = "patient-card";

      var meta = document.createElement("p");
      meta.className = "patient-meta";

      var name = document.createElement("span");
      name.className = "patient-name";
      name.textContent = (pat.first_name + " " + pat.last_name).trim();
      meta.appendChild(name);

      var details = [pat.gender, pat.phone]
        .filter(function (s) {
          return s;
        })
        .join(" · ");
      if (details) {
        meta.appendChild(document.createTextNode(" — " + details));
      }

      var dob = document.createElement("span");
      dob.className = "patient-date";
      dob.textContent = "DOB " + formatDate(pat.date_of_birth);
      meta.appendChild(dob);

      card.appendChild(meta);
      patientsList.appendChild(card);
    });
  }

  function loadPatients() {
    return api("/api/patients")
      .then(function (data) {
        if (data.length === 0) {
          patientsCount.textContent = "No patients entered yet.";
        } else if (data.length === 1) {
          patientsCount.textContent = "1 patient entered";
        } else {
          patientsCount.textContent = data.length + " patients entered";
        }
        renderPatients(data);
      })
      .catch(function () {
        patientsCount.textContent =
          "Could not load recent patients right now.";
      });
  }

  dobInput.max = todayISO();
  loadPatients();
})();
