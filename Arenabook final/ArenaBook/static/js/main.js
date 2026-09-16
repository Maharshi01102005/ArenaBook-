/* ArenaBook front-end behaviour */
(function () {
    "use strict";

    // ---- auto dismiss flash messages ------------------------------------
    document.querySelectorAll(".flash-wrap .alert").forEach(function (el) {
        setTimeout(function () {
            if (window.bootstrap && bootstrap.Alert) {
                bootstrap.Alert.getOrCreateInstance(el).close();
            }
        }, 6000);
    });

    // ---- venue gallery ---------------------------------------------------
    var mainImage = document.getElementById("galleryMain");
    document.querySelectorAll("[data-gallery-thumb]").forEach(function (thumb) {
        thumb.addEventListener("click", function () {
            if (!mainImage) return;
            mainImage.src = thumb.dataset.full || thumb.src;
            document.querySelectorAll("[data-gallery-thumb]").forEach(function (t) {
                t.classList.remove("active");
            });
            thumb.classList.add("active");
        });
    });

    // ---- booking slot picker --------------------------------------------
    var slotWrap = document.getElementById("slotGrid");
    var dateInput = document.getElementById("id_booking_date");
    var startInput = document.getElementById("id_start_time");
    var endInput = document.getElementById("id_end_time");
    var priceOut = document.getElementById("priceEstimate");
    var pricePerHour = slotWrap ? parseFloat(slotWrap.dataset.price || "0") : 0;
    var slotUrl = slotWrap ? slotWrap.dataset.url : null;

    function updateEstimate() {
        if (!priceOut || !startInput || !endInput) return;
        var s = startInput.value, e = endInput.value;
        if (!s || !e) { priceOut.textContent = "--"; return; }
        var start = new Date("2000-01-01T" + s);
        var end = new Date("2000-01-01T" + e);
        var hours = (end - start) / 3600000;
        if (hours <= 0) { priceOut.textContent = "--"; return; }
        priceOut.textContent = "₹ " + (hours * pricePerHour).toFixed(2);
    }

    function bindChips() {
        document.querySelectorAll(".slot-chip:not(.taken)").forEach(function (chip) {
            chip.addEventListener("click", function () {
                document.querySelectorAll(".slot-chip").forEach(function (c) {
                    c.classList.remove("selected");
                });
                chip.classList.add("selected");
                if (startInput) startInput.value = chip.dataset.start;
                if (endInput) endInput.value = chip.dataset.end;
                updateEstimate();
            });
        });
    }

    function loadSlots() {
        if (!slotWrap || !slotUrl || !dateInput || !dateInput.value) return;
        slotWrap.innerHTML = '<div class="text-muted-soft small py-2">Loading slots…</div>';
        fetch(slotUrl + "?date=" + encodeURIComponent(dateInput.value))
            .then(function (r) { return r.json(); })
            .then(function (data) {
                slotWrap.innerHTML = "";
                if (!data.slots || !data.slots.length) {
                    slotWrap.innerHTML = '<div class="text-muted-soft small">No slots configured for this venue.</div>';
                    return;
                }
                data.slots.forEach(function (slot) {
                    var chip = document.createElement("div");
                    chip.className = "slot-chip" + (slot.taken ? " taken" : "");
                    chip.textContent = slot.label;
                    chip.dataset.start = slot.start;
                    chip.dataset.end = slot.end;
                    if (slot.taken) chip.title = "Already booked";
                    slotWrap.appendChild(chip);
                });
                bindChips();
            })
            .catch(function () {
                slotWrap.innerHTML = '<div class="text-danger small">Slots could not be loaded. Pick a time manually.</div>';
            });
    }

    if (dateInput) dateInput.addEventListener("change", loadSlots);
    if (startInput) startInput.addEventListener("change", updateEstimate);
    if (endInput) endInput.addEventListener("change", updateEstimate);
    bindChips();
    updateEstimate();

    // ---- country / state / city chained selects --------------------------
    var countrySelect = document.getElementById("id_country");
    var stateSelect = document.getElementById("id_state");
    var citySelect = document.getElementById("id_city");

    function fill(select, rows, placeholder) {
        if (!select) return;
        select.innerHTML = '<option value="">' + placeholder + "</option>";
        rows.forEach(function (row) {
            var opt = document.createElement("option");
            opt.value = row.id;
            opt.textContent = row.name;
            select.appendChild(opt);
        });
    }

    if (countrySelect && stateSelect) {
        countrySelect.addEventListener("change", function () {
            fill(stateSelect, [], "Select state");
            fill(citySelect, [], "Select city");
            if (!countrySelect.value) return;
            fetch("/ajax/states/?country=" + countrySelect.value)
                .then(function (r) { return r.json(); })
                .then(function (rows) { fill(stateSelect, rows, "Select state"); });
        });
    }

    if (stateSelect && citySelect) {
        stateSelect.addEventListener("change", function () {
            fill(citySelect, [], "Select city");
            if (!stateSelect.value) return;
            fetch("/ajax/cities/?state=" + stateSelect.value)
                .then(function (r) { return r.json(); })
                .then(function (rows) { fill(citySelect, rows, "Select city"); });
        });
    }

    // ---- star rating widget ---------------------------------------------
    var ratingField = document.getElementById("id_rating");
    document.querySelectorAll("[data-rating]").forEach(function (input) {
        input.addEventListener("change", function () {
            if (ratingField) ratingField.value = input.value;
        });
    });

    // ---- admin sidebar toggle -------------------------------------------
    var sideToggle = document.getElementById("sideToggle");
    var side = document.getElementById("adminSide");
    var backdrop = document.getElementById("adminBackdrop");
    function closeSide() {
        if (side) side.classList.remove("open");
        if (backdrop) backdrop.classList.remove("show");
    }
    if (sideToggle && side) {
        sideToggle.addEventListener("click", function () {
            side.classList.toggle("open");
            if (backdrop) backdrop.classList.toggle("show");
        });
    }
    if (backdrop) backdrop.addEventListener("click", closeSide);

    // ---- confirm before destructive submits ------------------------------
    document.querySelectorAll("form[data-confirm]").forEach(function (form) {
        form.addEventListener("submit", function (event) {
            if (!window.confirm(form.dataset.confirm)) event.preventDefault();
        });
    });

    // ---- card number formatting on the payment page ----------------------
    var cardNumber = document.getElementById("id_card_number");
    if (cardNumber) {
        cardNumber.addEventListener("input", function () {
            var digits = cardNumber.value.replace(/\D/g, "").slice(0, 16);
            cardNumber.value = digits.replace(/(.{4})/g, "$1 ").trim();
        });
    }
    var expiry = document.getElementById("id_expiry");
    if (expiry) {
        expiry.addEventListener("input", function () {
            var digits = expiry.value.replace(/\D/g, "").slice(0, 4);
            expiry.value = digits.length > 2 ? digits.slice(0, 2) + "/" + digits.slice(2) : digits;
        });
    }

    // ---- payment method panels ------------------------------------------
    function syncPaymentPanels() {
        var checked = document.querySelector('input[name="payment_method"]:checked');
        var cardPanel = document.getElementById("cardPanel");
        if (!checked || !cardPanel) return;
        var isCard = checked.value === "credit_card" || checked.value === "debit_card";
        cardPanel.style.display = isCard ? "block" : "none";
    }
    document.querySelectorAll('input[name="payment_method"]').forEach(function (input) {
        input.addEventListener("change", syncPaymentPanels);
    });
    syncPaymentPanels();
})();
