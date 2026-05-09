$(function () {
  bindOptionCardStyles();
  bindProceedButtonState();
  bindStartButtonState();
  bindMealOrderActivity();
  bindPredictionActivity();
  bindChartToggle();
});

function bindOptionCardStyles() {
  $(".quiz-option-form input[type='radio']").on("change", function () {
    const groupName = $(this).attr("name");
    $(`.quiz-option-form input[name='${groupName}']`).each(function () {
      $(this).closest(".option-card").removeClass("is-selected");
    });
    if ($(this).is(":checked")) {
      $(this).closest(".option-card").addClass("is-selected");
    }
  });

  $(".quiz-option-form input[type='radio']:checked").each(function () {
    $(this).closest(".option-card").addClass("is-selected");
  });
}

function bindProceedButtonState() {
  const forms = $(".quiz-option-form");
  if (!forms.length) {
    return;
  }

  forms.each(function () {
    const form = $(this);
    const submitButton = form.find(".proceed-button");
    const radios = form.find("input[type='radio'][name='choice_id']");

    if (!radios.length || !submitButton.length) {
      return;
    }

    function refreshButtonState() {
      submitButton.prop("disabled", radios.filter(":checked").length === 0);
    }

    radios.on("change", refreshButtonState);
    refreshButtonState();
  });
}

function bindStartButtonState() {
  const startForm = $("#start-form");
  const startButton = $("#start-button");
  if (!startForm.length || !startButton.length) {
    return;
  }

  startForm.on("submit", function () {
    window.setTimeout(function () {
      startButton.prop("disabled", true);
      startButton.text("Starting...");
    }, 0);
  });
}

function logInteraction(eventType, details) {
  if (!window.fetch) {
    return;
  }

  fetch("/api/event", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      event_type: eventType,
      details: details || {},
    }),
  }).catch(function () {
    // Interaction logging is helpful for the demo, but it should never block learning.
  });
}

function bindMealOrderActivity() {
  const forms = $(".meal-order-form");
  if (!forms.length) {
    return;
  }

  forms.each(function () {
    const form = $(this);
    const board = form.find(".meal-order-board");
    const input = form.find(".order-input");
    let draggedCard = null;

    function cards() {
      return board.find(".meal-order-card");
    }

    function refreshOrder() {
      const orderIds = cards()
        .map(function () {
          return $(this).data("order-id");
        })
        .get();

      input.val(orderIds.join(","));

      cards().each(function (index) {
        const card = $(this);
        card.find(".meal-order-position").text(`Position ${index + 1}`);
        card.find(".move-up").prop("disabled", index === 0);
        card.find(".move-down").prop("disabled", index === cards().length - 1);
      });
    }

    function moveCard(card, direction) {
      if (direction === "up") {
        const previous = card.prev(".meal-order-card");
        if (previous.length) {
          card.insertBefore(previous);
        }
      } else {
        const next = card.next(".meal-order-card");
        if (next.length) {
          card.insertAfter(next);
        }
      }
      refreshOrder();
      logInteraction("meal_order_rearranged", { order_ids: input.val().split(",") });
    }

    board.on("click", ".move-up", function () {
      moveCard($(this).closest(".meal-order-card"), "up");
    });

    board.on("click", ".move-down", function () {
      moveCard($(this).closest(".meal-order-card"), "down");
    });

    board.on("dragstart", ".meal-order-card", function (event) {
      draggedCard = this;
      $(this).addClass("is-dragging");
      event.originalEvent.dataTransfer.effectAllowed = "move";
    });

    board.on("dragend", ".meal-order-card", function () {
      $(this).removeClass("is-dragging");
      draggedCard = null;
      refreshOrder();
      logInteraction("meal_order_rearranged", { order_ids: input.val().split(",") });
    });

    board.on("dragover", ".meal-order-card", function (event) {
      event.preventDefault();
      if (!draggedCard || draggedCard === this) {
        return;
      }

      const target = $(this);
      const targetMiddle = target.offset().top + target.outerHeight() / 2;
      if (event.originalEvent.pageY < targetMiddle) {
        target.before(draggedCard);
      } else {
        target.after(draggedCard);
      }
    });

    refreshOrder();
  });
}

function bindPredictionActivity() {
  $(".prediction-button").on("click", function () {
    const button = $(this);
    const panel = button.closest("[data-interaction-name]");
    const prediction = button.data("prediction");
    const response = panel.find(".prediction-response");

    panel.find(".prediction-button").removeClass("active");
    button.addClass("active");

    if (prediction === "sharp") {
      response.text("Good prediction: carb-first meals are more likely to create a sharper post-meal rise.");
    } else if (prediction === "gentle") {
      response.text("That is the goal for fiber/protein-first eating: a slower, gentler rise.");
    } else {
      response.text("Reasonable uncertainty. Use the chart below to compare the two patterns.");
    }

    logInteraction("glucose_prediction_selected", { prediction: prediction });
  });
}

function bindChartToggle() {
  $(".chart-toggle").on("click", function () {
    const button = $(this);
    const panel = button.closest("[data-chart-panel]");
    const curveId = button.data("curve");

    panel.find(".chart-toggle").removeClass("active");
    button.addClass("active");

    panel.find(".chart-curve").removeClass("active");
    panel.find(`[data-curve-path='${curveId}']`).addClass("active");

    panel.find(".chart-readout-label").text(button.data("label"));
    panel.find(".chart-readout-summary").text(button.data("summary"));

    logInteraction("glucose_chart_toggled", {
      curve: curveId,
      peak: button.data("peak"),
    });
  });
}
