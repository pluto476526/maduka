(function($) {
    'use strict';

    // Initialize tooltips
    $('[data-toggle="tooltip"]').tooltip();

    // Light/Dark theme toggle
    $('.light-dark-toggle').on('click', function() {
        $(this).toggleClass('active');
    });

    // Right sidebar toggle
    $('.rightbar .rightbar-link').on('click', function() {
        $('.rightbar').addClass('open');
    });

    $('.rightbar .close-sidebar').on('click', function() {
        $('.rightbar').removeClass('open');
    });

    // Chat sidebar toggle
    $('.chat-body .show-user-detail').on('click', function() {
        $('.main ').toggleClass('open-chat-sidebar');
    });

    $('.close-chat-sidebar').on('click', function() {
        $('.main ').removeClass('open-chat-sidebar');
    });

    // User sidebar toggle
    $('.chat-body .add-user-btn').on('click', function() {
        $('.main ').toggleClass('open-user-sidebar');
    });

    $('.close-chat-sidebar').on('click', function() {
        $('.main ').removeClass('open-user-sidebar');
    });

    // Sidebar menu toggle
    $('.sidebar-toggle-btn').on('click', function() {
        $('body ').toggleClass('open-sidebar-menu');
    });

    // Skin theme switcher
    $(document).ready(function() {
        $('.choose-skin li').on('click', function() {
            var $body = $('#layout');
            var $this = $(this);
            var existTheme = $('.choose-skin li.active').data('theme');
            $('.choose-skin li').removeClass('active');
            $body.removeClass('theme-' + existTheme);
            $this.addClass('active');
            var newTheme = $('.choose-skin li.active').data('theme');
            $body.addClass('theme-' + newTheme);
        });
    });

    // Menu toggle
    $(document).ready(function() {
        $('.menu-toggle').on('click', function(e) {
            var $this = $(this);
            var $content = $this.next();
            if ($($this.parents('ul')[0]).hasClass('list')) {
                var $not = $(e.target).hasClass('menu-toggle') ? e.target : $(e.target).parents('.menu-toggle');
                $.each($('.menu-toggle.toggled').not($not).next(), function(i, val) {
                    if ($(val).is(':visible')) {
                        $(val).prev().toggleClass('toggled');
                        $(val).slideUp();
                    }
                });
            }
            $this.toggleClass('toggled');
            $content.slideToggle(320);
        });
    });

    // Mini calendar initialization
    $('#mini-calendar').datepicker({
        todayHighlight: true,
        beforeShowDay: function(date) {
            if (date.getMonth() == (new Date()).getMonth()) {
                switch (date.getDate()) {
                    case 4:
                        return { tooltip: 'Example tooltip', classes: 'active' };
                    case 8:
                        return false;
                    case 12:
                        return "green";
                }
            }
        }
    });

    // Theme switching functionality with localStorage persistence
    var toggleSwitch = document.querySelector('.light-dark-toggle input[type="checkbox"]');
    var currentTheme = localStorage.getItem('theme');

    // Apply saved theme on page load
    if (currentTheme) {
        document.documentElement.setAttribute('data-theme', currentTheme);
        if (currentTheme === 'dark') {
            toggleSwitch.checked = true;
        }
    }

    // Switch theme and store preference
    function switchTheme(e) {
        if (e.target.checked) {
            document.documentElement.setAttribute('data-theme', 'dark');
            localStorage.setItem('theme', 'dark');
        } else {
            document.documentElement.setAttribute('data-theme', 'light');
            localStorage.setItem('theme', 'light');
        }
    }

    // Event listener for theme switch
    toggleSwitch.addEventListener('change', switchTheme, false);

})(jQuery);



