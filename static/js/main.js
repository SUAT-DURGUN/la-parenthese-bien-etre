window.addEventListener('scroll', () => {
    const navbar = document.getElementById('navbar');
    if (window.scrollY > 50) navbar.classList.add('scrolled');
    else navbar.classList.remove('scrolled');
});
function toggleMenu() {
    document.getElementById('navLinks').classList.toggle('active');
}
document.querySelectorAll('.nav-links a').forEach(link => {
    link.addEventListener('click', () => document.getElementById('navLinks').classList.remove('active'));
});
setTimeout(() => {
    document.querySelectorAll('.flash-message').forEach(msg => { msg.style.opacity = '0'; setTimeout(() => msg.remove(), 500); });
}, 5000);
console.log('La Parenthese Bien-Etre loaded!');
