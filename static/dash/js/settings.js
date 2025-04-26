// (function($) {
//   'use strict';
//   $(function() {
//     $(".nav-settings").on("click", function() {
//       $("#right-sidebar").toggleClass("open");
//     });
//     $(".settings-close").on("click", function() {
//       $("#right-sidebar,#theme-settings").removeClass("open");
//     });
//
//     $("#settings-trigger").on("click" , function(){
//       $("#theme-settings").toggleClass("open");
//     });
//
//
//     //background constants
//     var navbar_classes = "navbar-danger navbar-success navbar-warning navbar-dark navbar-light navbar-primary navbar-info navbar-pink";
//     var sidebar_classes = "sidebar-light sidebar-dark";
//     var $body = $("body");
//
//     //sidebar backgrounds
//     $("#sidebar-light-theme").on("click" , function(){
//       $body.removeClass(sidebar_classes);
//       $body.addClass("sidebar-light");
//       $(".sidebar-bg-options").removeClass("selected");
//       $(this).addClass("selected");
//     });
//     $("#sidebar-dark-theme").on("click" , function(){
//       $body.removeClass(sidebar_classes);
//       $body.addClass("sidebar-dark");
//       $(".sidebar-bg-options").removeClass("selected");
//       $(this).addClass("selected");
//     });
//
//
//     //Navbar Backgrounds
//     $(".tiles.primary").on("click" , function(){
//       $(".navbar").removeClass(navbar_classes);
//       $(".navbar").addClass("navbar-primary");
//       $(".tiles").removeClass("selected");
//       $(this).addClass("selected");
//     });
//     $(".tiles.success").on("click" , function(){
//       $(".navbar").removeClass(navbar_classes);
//       $(".navbar").addClass("navbar-success");
//       $(".tiles").removeClass("selected");
//       $(this).addClass("selected");
//     });
//     $(".tiles.warning").on("click" , function(){
//       $(".navbar").removeClass(navbar_classes);
//       $(".navbar").addClass("navbar-warning");
//       $(".tiles").removeClass("selected");
//       $(this).addClass("selected");
//     });
//     $(".tiles.danger").on("click" , function(){
//       $(".navbar").removeClass(navbar_classes);
//       $(".navbar").addClass("navbar-danger");
//       $(".tiles").removeClass("selected");
//       $(this).addClass("selected");
//     });
//     $(".tiles.light").on("click" , function(){
//       $(".navbar").removeClass(navbar_classes);
//       $(".navbar").addClass("navbar-light");
//       $(".tiles").removeClass("selected");
//       $(this).addClass("selected");
//     });
//     $(".tiles.info").on("click" , function(){
//       $(".navbar").removeClass(navbar_classes);
//       $(".navbar").addClass("navbar-info");
//       $(".tiles").removeClass("selected");
//       $(this).addClass("selected");
//     });
//     $(".tiles.dark").on("click" , function(){
//       $(".navbar").removeClass(navbar_classes);
//       $(".navbar").addClass("navbar-dark");
//       $(".tiles").removeClass("selected");
//       $(this).addClass("selected");
//     });
//     $(".tiles.default").on("click" , function(){
//       $(".navbar").removeClass(navbar_classes);
//       $(".tiles").removeClass("selected");
//       $(this).addClass("selected");
//     });
//   });
// })(jQuery);





(function($) {
  'use strict';
  $(function() {
    // Helper function to apply stored themes from localStorage
    function applyStoredThemes() {
      var storedNavbarClass = localStorage.getItem("navbarClass");
      var storedSidebarClass = localStorage.getItem("sidebarClass");

      // Apply stored navbar class if exists
      if (storedNavbarClass) {
        $(".navbar").removeClass("navbar-danger navbar-success navbar-warning navbar-dark navbar-light navbar-primary navbar-info navbar-pink");
        $(".navbar").addClass(storedNavbarClass);
        $(".tiles").removeClass("selected");
        $(".tiles." + storedNavbarClass).addClass("selected");
      }

      // Apply stored sidebar class if exists
      if (storedSidebarClass) {
        $("body").removeClass("sidebar-light sidebar-dark");
        $("body").addClass(storedSidebarClass);
        $(".sidebar-bg-options").removeClass("selected");
        $("#" + storedSidebarClass + "-theme").addClass("selected");
      }
    }

    // Apply stored themes when the page loads
    applyStoredThemes();

    // Settings toggle actions
    $(".nav-settings").on("click", function() {
      $("#right-sidebar").toggleClass("open");
    });

    $(".settings-close").on("click", function() {
      $("#right-sidebar,#theme-settings").removeClass("open");
    });

    $("#settings-trigger").on("click", function() {
      $("#theme-settings").toggleClass("open");
    });

    // Background constants for navbar and sidebar
    var navbar_classes = "navbar-danger navbar-success navbar-warning navbar-dark navbar-light navbar-primary navbar-info navbar-pink";
    var sidebar_classes = "sidebar-light sidebar-dark";

    // Sidebar theme selection
    $("#sidebar-light-theme").on("click", function() {
      $("body").removeClass(sidebar_classes);
      $("body").addClass("sidebar-light");
      localStorage.setItem("sidebarClass", "sidebar-light"); // Store sidebar preference
      $(".sidebar-bg-options").removeClass("selected");
      $(this).addClass("selected");
    });

    $("#sidebar-dark-theme").on("click", function() {
      $("body").removeClass(sidebar_classes);
      $("body").addClass("sidebar-dark");
      localStorage.setItem("sidebarClass", "sidebar-dark"); // Store sidebar preference
      $(".sidebar-bg-options").removeClass("selected");
      $(this).addClass("selected");
    });

    // Navbar theme selection
    $(".tiles.primary").on("click", function() {
      $(".navbar").removeClass(navbar_classes);
      $(".navbar").addClass("navbar-primary");
      localStorage.setItem("navbarClass", "navbar-primary"); // Store navbar preference
      $(".tiles").removeClass("selected");
      $(this).addClass("selected");
    });

    $(".tiles.success").on("click", function() {
      $(".navbar").removeClass(navbar_classes);
      $(".navbar").addClass("navbar-success");
      localStorage.setItem("navbarClass", "navbar-success"); // Store navbar preference
      $(".tiles").removeClass("selected");
      $(this).addClass("selected");
    });

    $(".tiles.warning").on("click", function() {
      $(".navbar").removeClass(navbar_classes);
      $(".navbar").addClass("navbar-warning");
      localStorage.setItem("navbarClass", "navbar-warning"); // Store navbar preference
      $(".tiles").removeClass("selected");
      $(this).addClass("selected");
    });

    $(".tiles.danger").on("click", function() {
      $(".navbar").removeClass(navbar_classes);
      $(".navbar").addClass("navbar-danger");
      localStorage.setItem("navbarClass", "navbar-danger"); // Store navbar preference
      $(".tiles").removeClass("selected");
      $(this).addClass("selected");
    });

    $(".tiles.light").on("click", function() {
      $(".navbar").removeClass(navbar_classes);
      $(".navbar").addClass("navbar-light");
      localStorage.setItem("navbarClass", "navbar-light"); // Store navbar preference
      $(".tiles").removeClass("selected");
      $(this).addClass("selected");
    });

    $(".tiles.info").on("click", function() {
      $(".navbar").removeClass(navbar_classes);
      $(".navbar").addClass("navbar-info");
      localStorage.setItem("navbarClass", "navbar-info"); // Store navbar preference
      $(".tiles").removeClass("selected");
      $(this).addClass("selected");
    });

    $(".tiles.dark").on("click", function() {
      $(".navbar").removeClass(navbar_classes);
      $(".navbar").addClass("navbar-dark");
      localStorage.setItem("navbarClass", "navbar-dark"); // Store navbar preference
      $(".tiles").removeClass("selected");
      $(this).addClass("selected");
    });

    $(".tiles.default").on("click", function() {
      $(".navbar").removeClass(navbar_classes);
      $(".tiles").removeClass("selected");
      $(this).addClass("selected");
      localStorage.removeItem("navbarClass"); // Remove navbar preference if reset
    });
  });
})(jQuery);
