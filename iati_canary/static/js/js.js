(function($) {
  "use strict"; // Start of use strict

  // Smooth scrolling using jQuery easing
  $('a.js-scroll-trigger[href*="#"]:not([href="#"])').click(function() {
    if (location.pathname.replace(/^\//, '') == this.pathname.replace(/^\//, '') && location.hostname == this.hostname) {
      var target = $(this.hash);
      target = target.length ? target : $('[name=' + this.hash.slice(1) + ']');
      if (target.length) {
        $('html, body').animate({
          scrollTop: (target.offset().top - 70)
        }, 1000, "easeInOutExpo");
        return false;
      }
    }
  });

  // Closes responsive menu when a scroll trigger link is clicked
  $('.js-scroll-trigger').click(function() {
    $('.navbar-collapse').collapse('hide');
  });

  // Activate scrollspy to add active class to navbar items on scroll
  $('body').scrollspy({
    target: '#mainNav',
    offset: 80
  });

  // Collapse Navbar
  var navbarCollapse = function() {
    if ($("#mainNav").offset().top > 100) {
      $("#mainNav").addClass("navbar-shrink");
    } else {
      $("#mainNav").removeClass("navbar-shrink");
    }
  };
  // Collapse now if page is not at top
  navbarCollapse();
  // Collapse the navbar when page is scrolled
  $(window).scroll(navbarCollapse);

  $('#show-publisher').select2({
    theme: 'bootstrap4',
    placeholder: $('#show-publisher').attr('placeholder'),
    ajax: {
      delay: 100,
      url: '/publishers.json?errors=true',
      processResults: function (data) {
        data.results = $.map(data.results, function (d) {
          var text = d.text;
          if (d.error_count === 1) {
            text += ' (1 broken dataset)';
          } else if (d.error_count > 1) {
            text += ' (' + d.error_count + ' broken datasets)';
          }
          return {
            id: d.id,
            text: text
          };
        });
        return data;
      }
    }
  }).on('select2:select', function (e) {
    window.location = '/publisher/' + e.params.data.id;
  });

  $('#select-publisher').select2({
    theme: 'bootstrap4',
    placeholder: $('#select-publisher').attr('placeholder'),
    ajax: {
      delay: 100,
      url: '/publishers.json'
    }
  });

})(jQuery); // End of use strict
