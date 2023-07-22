/**
 * Toggles the side bar on the left side of website
 */
function toggleNavbar() {
  var navbar = document.getElementById("side-navbar");
  navbar.classList.toggle("show");
}

function renderHTML() {
  const htmlString = document.getElementById('generated-blog-content').innerHTML; // The HTML string

  // Step 1: Get the reference to the <div> element
  const div = document.getElementById('generated-blog-content');

  // Step 2: Set the HTML content of the <div> using innerHTML
  div.innerHTML = htmlString;
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