jQuery(document).ready(function($) {
    // Handle form submission
    $('#my-form').submit( function(e) {
      e.preventDefault();
  
      // Get form data
      var formData = $(this).serialize();
      console.log(formData);
  
      // AJAX request
      $.ajax({
        url: 'http://localhost:5000/process-form',
        type: 'POST',
        data: {
          data: formData,
        },
        success: function(response) {
          $('#responseContainer').text(response['name'] + ' ' + response['email']);
          // Handle the response
          console.log(response);
        }
      });
    });
  });
  