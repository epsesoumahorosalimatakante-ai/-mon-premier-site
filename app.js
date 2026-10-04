const CLE = "mes-taches";

const formulaire = document.getElementById("formulaire");
const saisie = document.getElementById("saisie");
const liste = document.getElementById("liste");
const vide = document.getElementById("vide");
const compteur = document.getElementById("compteur");
const boutonEffacer = document.getElementById("effacer");
const boutonsFiltre = document.querySelectorAll("[data-filtre]");

let taches = charger();
let filtre = "toutes";

function charger() {
  try {
    return JSON.parse(localStorage.getItem(CLE)) || [];
  } catch {
    return [];
  }
}

function sauvegarder() {
  try {
    localStorage.setItem(CLE, JSON.stringify(taches));
  } catch {
    // Stockage indisponible (navigation privée) : l'appli fonctionne quand même.
  }
}

function afficher() {
  const visibles = taches.filter((t) =>
    filtre === "actives" ? !t.terminee : filtre === "terminees" ? t.terminee : true
  );

  liste.innerHTML = "";
  for (const tache of visibles) {
    const li = document.createElement("li");
    li.classList.toggle("terminee", tache.terminee);

    const case_ = document.createElement("input");
    case_.type = "checkbox";
    case_.checked = tache.terminee;
    case_.setAttribute("aria-label", "Marquer comme terminée");
    case_.addEventListener("change", () => {
      tache.terminee = case_.checked;
      sauvegarder();
      afficher();
    });

    const texte = document.createElement("span");
    texte.className = "texte";
    texte.textContent = tache.texte;

    const supprimer = document.createElement("button");
    supprimer.className = "supprimer";
    supprimer.type = "button";
    supprimer.textContent = "×";
    supprimer.setAttribute("aria-label", "Supprimer");
    supprimer.addEventListener("click", () => {
      taches = taches.filter((t) => t.id !== tache.id);
      sauvegarder();
      afficher();
    });

    li.append(case_, texte, supprimer);
    liste.append(li);
  }

  vide.hidden = visibles.length > 0;

  const restantes = taches.filter((t) => !t.terminee).length;
  compteur.textContent =
    taches.length === 0
      ? "Aucune tâche"
      : `${restantes} à faire sur ${taches.length}`;
}

formulaire.addEventListener("submit", (e) => {
  e.preventDefault();
  const texte = saisie.value.trim();
  if (!texte) return;
  taches.push({ id: Date.now() + Math.random(), texte, terminee: false });
  saisie.value = "";
  sauvegarder();
  afficher();
});

boutonsFiltre.forEach((bouton) => {
  bouton.addEventListener("click", () => {
    filtre = bouton.dataset.filtre;
    boutonsFiltre.forEach((b) => b.classList.toggle("actif", b === bouton));
    afficher();
  });
});

boutonEffacer.addEventListener("click", () => {
  taches = taches.filter((t) => !t.terminee);
  sauvegarder();
  afficher();
});

afficher();
