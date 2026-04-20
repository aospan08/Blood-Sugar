$(function () {
  bindOptionCardStyles();
  bindProceedButtonState();
  bindStartButtonState();
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
