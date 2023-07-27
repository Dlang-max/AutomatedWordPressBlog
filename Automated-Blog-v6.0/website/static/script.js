const toggleButton = document.getElementsByClassName('toggle-button')[0];
const navbarLinks = document.getElementsByClassName('navbar-links')[0];

toggleButton.addEventListener('click', () => {
  navbarLinks.classList.toggle('active');
});

// function captureDivContent() {
//   const divContent = document.getElementById('generated').innerHTML;
//   document.getElementById('divContentInput').value = divContent;
// }

document.getElementById('generate').addEventListener('submit', function (event) {
  event.preventDefault();
  var button = document.getElementById('generate-button');

  button.disabled = true;
  button.innerHTML = "Generating...";
  event.target.submit();
});


// document.getElementById('generated-content').addEventListener('submit', function (event) {
//   event.preventDefault(); 
//   captureDivContent();    
//   this.submit();         
// });


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