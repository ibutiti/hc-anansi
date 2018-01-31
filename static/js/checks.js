$(function() {

    var MINUTE = { name: "minute", nsecs: 60 };
    var HOUR = { name: "hour", nsecs: MINUTE.nsecs * 60 };
    var DAY = { name: "day", nsecs: HOUR.nsecs * 24 };
    var WEEK = { name: "week", nsecs: DAY.nsecs * 7 };
    var MONTH = { name: "month", nsecs: (WEEK.nsecs * 4) + (DAY.nsecs * 2) };
    var UNITS = [MONTH, WEEK, DAY, HOUR, MINUTE];

    var secsToText = function(total) {
        var remainingSeconds = Math.floor(total);
        var result = "";
        for (var i = 0, unit; unit = UNITS[i]; i++) {
            if (unit === WEEK && remainingSeconds % unit.nsecs != 0) {
                // Say "8 days" instead of "1 week 1 day"
                continue
            }

            var count = Math.floor(remainingSeconds / unit.nsecs);
            remainingSeconds = remainingSeconds % unit.nsecs;

            if (count == 1) {
                result += "1 " + unit.name + " ";
            }

            if (count > 1) {
                result += count + " " + unit.name + "s ";
            }
        }

        return result;
    }

    //global scale values
    durationA = 60;
    durationB = 1800;
    durationC = 3600;
    durationD = 43200;
    durationE = 86400;
    durationF = 604800;
    durationG = 2592000;
    durationH = 5184000;

    //function that constructs the slider for period timeouts
    var periodSlider = document.getElementById("period-slider");
    noUiSlider.create(periodSlider, {
        start: [20],
        connect: "lower",
        range: {
            'min': [durationA, durationA],
            '33%': [durationC, durationC],
            '66%': [durationE, durationE],
            '72%': [durationF, durationF],
            'max': durationH,
        },
        pips: {
            mode: 'values',
            values: [durationA, durationB, durationC, durationD,
                durationE, durationG, durationH
            ],
            density: 4,
            format: {
                to: secsToText,
                from: function() {}
            }
        }
    });

    periodSlider.noUiSlider.on("update", function(a, b, value) {
        var rounded = Math.round(value);
        $("#period-slider-value").text(secsToText(rounded));
        $("#update-timeout-timeout").val(rounded);
    });


    var graceSlider = document.getElementById("grace-slider");
    noUiSlider.create(graceSlider, {
        start: [20],
        connect: "lower",
        range: {
            'min': [durationA, durationA],
            '33%': [durationC, durationC],
            '66%': [durationE, durationE],
            '72%': [durationF, durationF],
            'max': durationH,
        },
        pips: {
            mode: 'values',
            values: [durationA, durationB, durationC, durationD,
                durationE, durationG, durationH
            ],
            density: 4,
            format: {
                to: secsToText,
                from: function() {}
            }
        }
    });

    graceSlider.noUiSlider.on("update", function(a, b, value) {
        var rounded = Math.round(value);
        $("#grace-slider-value").text(secsToText(rounded));
        $("#update-timeout-grace").val(rounded);
    });

    // Nag slider setup
    var nagSlider = document.getElementById("nag-slider");
    noUiSlider.create(nagSlider, {
        start: [20],
        connect: 'lower',
        range: {
            'min': [durationA, durationA],
            '33%': [durationC, durationC],
            '66%': [durationE, durationE],
            '72%': [durationF, durationF],
            'max': durationH,
        },
        pips: {
            mode: 'values',
            values: [
                durationA, durationB, durationC, durationD,
                durationE, durationG, durationH
            ],
            density: 4,
            format: {
                to: secsToText,
                from: function() {}
            }
        }
    });

    nagSlider.noUiSlider.on("update", function(a, b, value) {
        var rounded = Math.round(value);
        $("#nag-slider-value").text(secsToText(rounded));
        $("#update-timeout-nag").val(rounded);
    });

    $('[data-toggle="tooltip"]').tooltip();

    $(".my-checks-name").click(function() {
        var $this = $(this);

        $("#update-name-form").attr("action", $this.data("url"));
        $("#update-name-input").val($this.data("name"));
        $("#update-tags-input").val($this.data("tags"));
        $('#update-name-modal').modal("show");
        $("#update-name-input").focus();

        return false;
    });

    $(".timeout-grace").click(function() {
        var $this = $(this);

        $("#update-timeout-form").attr("action", $this.data("url"));
        periodSlider.noUiSlider.set($this.data("timeout"));
        graceSlider.noUiSlider.set($this.data("grace"));
        nagSlider.noUiSlider.set($this.data("nag"));
        $('#update-timeout-modal').modal({ "show": true, "backdrop": "static" });

        return false;
    });

    $(".check-menu-remove").click(function() {
        var $this = $(this);

        $("#remove-check-form").attr("action", $this.data("url"));
        $(".remove-check-name").text($this.data("name"));
        $('#remove-check-modal').modal("show");

        return false;
    });

    $("button.clear-all").not(".unresolved").click(function() {
        // show all rows in all checks, hidden or not
        $("#checks-table tr.checks-row").show();
        $("#checks-list > li").show();

        // deactivate checks filter buttons in all tab
        $("#my-checks-tags button").removeClass('checked');
        $("#my-checks-tags button").removeClass('active');

    });

    $("button.clear-all.unresolved").click(function() {
        // show all rows in unresolved checks, hidden or not
        $("#unresolved-checks-table tr.checks-row").show();
        $("#unresolved-checks-list > li").show();

        // deactivate filter buttons in unresolved tab
        $("#my-unresolved-checks-tags button").removeClass('checked');
        $("#my-unresolved-checks-tags button").removeClass('active');

    });

    $("#my-checks-tags button").not(".clear-all").click(function() {
        // .active has not been updated yet by bootstrap code,
        // so cannot use it
        $(this).toggleClass("checked");


        // Make a list of currently checked tags:
        var checked = [];
        $("#my-checks-tags button.checked").each(function(index, el) {
            checked.push(el.textContent);
        });

        // No checked tags: show all
        if (checked.length == 0) {
            $("#checks-table tr.checks-row").show();
            $("#checks-list > li").show();
            return;
        }

        function applyFilters(index, element) {
            var tags = $(".my-checks-name", element).data("tags").split(" ");
            for (var i = 0, tag; tag = checked[i]; i++) {
                if (tags.indexOf(tag) == -1) {
                    $(element).hide();
                    return;
                }
            }

            $(element).show();
        }

        // Desktop: for each row, see if it needs to be shown or hidden
        $("#checks-table tr.checks-row").each(applyFilters);
        // Mobile: for each list item, see if it needs to be shown or hidden
        $("#checks-list > li").each(applyFilters);

    });

    $("#my-unresolved-checks-tags button").not(".clear-all").click(function() {
        // tags filter for unresolved checks
        // .active has not been updated yet by bootstrap code,
        // so cannot use it
        $(this).toggleClass("checked");

        // Make a list of currently checked tags:
        var checked = [];
        $("#my-unresolved-checks-tags button.checked").each(function(index, el) {
            checked.push(el.textContent);
        });

        // No checked tags: show all
        if (checked.length == 0) {
            $("#unresolved-checks-list > li").show();
            $("#unresolved-checks-table tr.checks-row").show();
            return;
        }

        function applyFilters(index, element) {
            var tags = $(".my-checks-name", element).data("tags").split(" ");
            for (var i = 0, tag; tag = checked[i]; i++) {
                if (tags.indexOf(tag) == -1) {
                    $(element).hide();
                    return;
                }
            }

            $(element).show();
        }

        // Desktop: for each row, see if it needs to be shown or hidden
        $("#unresolved-checks-table tr.checks-row").each(applyFilters);
        // Mobile: for each list item, see if it needs to be shown or hidden
        $("#unresolved-checks-list > li").each(applyFilters);

    });

    $(".pause-check").click(function(e) {
        var url = e.target.getAttribute("data-url");
        $("#pause-form").attr("action", url).submit();
        return false;
    });


    $(".usage-examples").click(function(e) {
        var a = e.target;
        var url = a.getAttribute("data-url");
        var email = a.getAttribute("data-email");

        $(".ex", "#show-usage-modal").text(url);
        $(".em", "#show-usage-modal").text(email);

        $("#show-usage-modal").modal("show");
        return false;
    });


    var clipboard = new Clipboard('button.copy-link');
    $("button.copy-link").mouseout(function(e) {
        setTimeout(function() {
            e.target.textContent = "copy";
        }, 300);
    })

    clipboard.on('success', function(e) {
        e.trigger.textContent = "copied!";
        e.clearSelection();
    });

    clipboard.on('error', function(e) {
        var text = e.trigger.getAttribute("data-clipboard-text");
        prompt("Press Ctrl+C to select:", text);
    });
});
