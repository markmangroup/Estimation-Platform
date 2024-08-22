// Check In
$(document).ready(function() {
    const qtyValue = 14
    // Function to validate quantity
    function validateQuantity(input, expected) {
        var value = input.val().trim(); // Trim whitespace
        if (value === "") {
            input.removeClass('match-quantity mismatch-quantity focused-quantity').addClass('empty-quantity');
            return false;
        }
        var numberValue = parseInt(value);
        if (isNaN(numberValue) || numberValue < 0 || numberValue > qtyValue) {
            input.removeClass('match-quantity focused-quantity').addClass('mismatch-quantity');
            return false;
        } else if (numberValue === expected) {
            input.removeClass('mismatch-quantity focused-quantity').addClass('match-quantity');
            return true;
        } else {
            input.removeClass('match-quantity focused-quantity').addClass('mismatch-quantity');
            return false;
        }
    }

    // Event delegation for input focus and blur
    $(document).on('focus', '.qty', function() {
        $('.qty').removeClass('focused-quantity');
        $(this).addClass('focused-quantity');
    }).on('blur', '.qty', function() {
        $(this).removeClass('focused-quantity');
        validateQuantity($(this), qtyValue);
    });

    // Event delegation for input change
    $(document).on('input', '.qty', function() {
        var inputValue = $(this).val();
        var numberValue = parseInt(inputValue);
        var outputText = $(this).siblings('small');

        missing_qty = qtyValue - numberValue
        const current = 1593;
        const minus = $(".minusQuantity");
        const revised = $(".revisedQuantity");
        minus.val(missing_qty);
        revised.val(current - missing_qty);

        if (parseInt(inputValue) < qtyValue) {
            outputText.html(`<span class="warning"><i class="ft-alert-triangle"></i> Quantity does not match, ${missing_qty} qty is missing!! </span> <br> <span style="color:darkslateblue;">Do stock adjustment?</span> <a data-toggle="modal" data-target="#stock_adjustment"><i class="ft-check success"></i></a>  <a><i class="ft-x danger"></i></a>`);
        } else {
            outputText.text('');
        }
    });

    // Initial validation on page load
    $('.qty').each(function() {
        validateQuantity($(this), qtyValue);
    });
});


// Check Out
$(document).ready(function() {
    const qty = 14;
    $(".checkout-qty").on('input', function() {
        const filteredValue = $(this).val().replace(/[^0-9]/g, '');
        $(this).val(filteredValue);
        const numberValue = parseInt(filteredValue, 10);

        if (filteredValue === "") {
            $("#quantityMessage").html('');
        } else if (numberValue !== qty) {
            $("#quantityMessage").html(`<span class="warning"><i class="ft-alert-triangle"></i> Quantity does not match, Please Resolve!! </span>`);
            console.log("Quantity doesn't  match, please resolve!!");
        } else if (numberValue === qty) {
            $("#quantityMessage").html('');
            console.log('Quantity matched!!');
        }
    });

    $(".checkout-qty").on('keypress', function(e) {
        if (e.which < 48 || e.which > 57) {
            e.preventDefault();
        }
    });

    $(".checkout-qty").on('paste', function(e) {
        e.preventDefault();
        const pasteData = (e.originalEvent || e).clipboardData.getData('text');
        const numericPasteData = pasteData.replace(/[^0-9]/g, '');
        document.execCommand('insertText', false, numericPasteData);
    });
});

// inspection-qty
$(document).ready(function() {
    const qtyValue = 14
    // Function to validate quantity
    function validateQuantity(input, expected) {
        var value = input.val().trim(); // Trim whitespace
        if (value === "") {
            input.removeClass('match-quantity mismatch-quantity focused-quantity').addClass('empty-quantity');
            return false;
        }
        var numberValue = parseInt(value);
        if (isNaN(numberValue) || numberValue < 0 || numberValue > qtyValue) {
            input.removeClass('match-quantity focused-quantity').addClass('mismatch-quantity');
            return false;
        } else if (numberValue === expected) {
            input.removeClass('mismatch-quantity focused-quantity').addClass('match-quantity');
            return true;
        } else {
            input.removeClass('match-quantity focused-quantity').addClass('mismatch-quantity');
            return false;
        }
    }

    // Event delegation for input focus and blur
    $(document).on('focus', '.inspection-qty', function() {
        $('.inspection-qty').removeClass('focused-quantity');
        $(this).addClass('focused-quantity');
    }).on('blur', '.inspection-qty', function() {
        $(this).removeClass('focused-quantity');
        validateQuantity($(this), qtyValue);
    });

    // Event delegation for input change
    $(document).on('input', '.inspection-qty', function() {
        var inputValue = $(this).val();
        var numberValue = parseInt(inputValue);
        var outputText = $(this).siblings('small');
        var markComplete = $(this).siblings('span.mark-completed');

        missing_qty = qtyValue - numberValue
        const current = 1593;
        const minus = $("#minusQuantity");
        const revised = $("#revisedQuantity");
        minus.val(missing_qty);
        revised.val(current - missing_qty);

        if (isNaN(numberValue) || inputValue.trim() === '' || parseInt(inputValue) < qtyValue) {
            outputText.html(`<span class="warning"><i class="ft-alert-triangle"></i> Quantity does not match, ${missing_qty} qty is missing!! </span> <br> <span style="color:darkslateblue;">Do stock adjustment?</span> <a data-toggle="modal" data-target="#inspection_stock_adjustment"><i class="ft-check success"></i></a>  <a><i class="ft-x danger"></i></a>`);
            markComplete.hide();
        }else {
            outputText.text('');
            markComplete.show();
        }
    });

    // Event delegation for mark completion
    $(document).on('click', 'a.marked', function() {
        console.log("-=-=-=-=-=-=-=-= Clicked");
        var $input = $(this).closest('td').find('.inspection-qty');
        var $markComplete = $(this).closest('td').find('span.mark-completed');

        $markComplete.hide();
        console.log("-=-=-=-=-=-=-=-= Hide");
        $input.prop('disabled', true);
        console.log("-=-=-=-=-=-=-=-= Disabled");
    });

    // Initial validation on page load
    $('.inspection-qty').each(function() {
        validateQuantity($(this), qtyValue);
    });
});