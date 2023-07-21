/**
 * Toggles the side bar on the left side of website
 */
function toggleNavbar() {
  var navbar = document.getElementById("side-navbar");
  navbar.classList.toggle("show");
}

function toggleBlogHub(){
  var svg = document.getElementById("blog-hub-arrow");
  var container = document.getElementById("blog-info-container"); 

  svg.classList.toggle("show")
  container.classList.toggle("show")
}

/**
 * Redirects user to stripe checkout
 */
fetch("/config")
.then((result) => { return result.json(); })
.then((data) => {

  const stripe = Stripe(data.publicKey);

  document.querySelector("#submitBtn").addEventListener("click", () => {

    fetch("/create-checkout-session")
    .then((result) => { return result.json(); })
    .then((data) => {
      console.log(data);

      return stripe.redirectToCheckout({sessionId: data.sessionId})
    })
    .then((res) => {
      console.log(res);
    });
  });
});