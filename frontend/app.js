
const API = "http://127.0.0.1:8000";

const $ = (id) => document.getElementById(id);


// 1. ESTADO GENERAL


const S = {
  movies: [],
  movie: null,
  functions: [],
  fn: null,
  seats: [],
  selected: new Set(),
  token: localStorage.getItem("cinenow_token"),
  mode: "login"
};


// 2. UTILIDADES


const money = (n) =>
  new Intl.NumberFormat("es-MX", {
    style: "currency",
    currency: "MXN"
  }).format(Number(n) || 0);

const id = (x) => String(x?._id ?? x?.id ?? "");

const esc = (s) =>
  String(s ?? "").replace(/[&<>"]/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;"
  })[c]);

const date = (s) => {
  const d = new Date(s);

  return isNaN(d.getTime())
    ? String(s ?? "")
    : d.toLocaleString("es-MX", {
        dateStyle: "medium",
        timeStyle: "short"
      });
};

function toast(message) {
  const el = $("toast");

  el.textContent = message;
  el.classList.add("show");

  setTimeout(() => {
    el.classList.remove("show");
  }, 2600);
}


// 3. CONEXIÓN CON FASTAPI


async function api(path, opt = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(opt.headers || {})
  };

  if (S.token) {
    headers.Authorization = "Bearer " + S.token;
  }

  const response = await fetch(API + path, {
    ...opt,
    headers
  });

  const text = await response.text();
  let data = {};

  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    data = { detail: text };
  }

  if (!response.ok) {
    let error =
      data.detail ||
      data.mensaje ||
      "Error " + response.status;

    if (Array.isArray(error)) {
      error = error.map((e) => {
        const campo = Array.isArray(e.loc)
          ? e.loc.join(".")
          : "";

        return (
          (campo ? campo + ": " : "") +
          (e.msg || JSON.stringify(e))
        );
      }).join(" | ");
    } else if (
      typeof error === "object" &&
      error !== null
    ) {
      error = error.msg || JSON.stringify(error);
    }

    throw new Error(String(error));
  }

  return data;
}


// 4. PELÍCULAS


async function movies() {
  const grid = $("movieGrid");

  grid.textContent = "Cargando películas...";

  try {
    const data = await api("/peliculas/");

    S.movies = Array.isArray(data)
      ? data
      : data.peliculas || [];

    if (!S.movies.length) {
      grid.textContent = "No hay películas registradas.";
      return;
    }

    grid.innerHTML = S.movies.map((m) => `
      <div class="card" data-m="${esc(id(m))}">
        
<div class="poster">
  ${
    (() => {
      const posters = {
        "interestelar": "interestelar.jpg",
        "el origen": "el-origen.jpg",
        "avatar: el camino del agua": "avatar-2.jpg",
        "spider-man: sin camino a casa": "spiderman.jpg",
        "coco": "coco.jpg",
        "intensamente 2": "intensamente-2.jpg",
        "duna: parte dos": "duna-2.jpg",
        "oppenheimer": "oppenheimer.jpg",
        "el conjuro": "el-conjuro.jpg",
        "jurassic world": "jurassic-world.jpg",
        "batman: el caballero de la noche": "batman.jpg",
        "super mario bros.: la película": "super-mario.jpg"
      };

      const titulo = m.titulo?.trim().toLowerCase();
      const archivo = posters[titulo];
      const imagen = archivo
        ? `img/peliculas/${archivo}`
        : m.poster_url;

      return imagen
        ? `<img src="${esc(imagen)}" alt="${esc(m.titulo)}" onerror="this.remove()">`
        : "🎬";
    })()
  }
</div>


        <div class="info">
          <h3>${esc(m.titulo)}</h3>

          <p>
            ${esc(m.duracion || "")} min ·
            ${esc(m.clasificacion || "")}
          </p>

          <b style="color:#ff967b">
            Ver funciones ↗
          </b>
        </div>
      </div>
    `).join("");

    document.querySelectorAll("[data-m]").forEach((card) => {
      card.onclick = () => openMovie(card.dataset.m);
    });

  } catch (error) {
    grid.textContent =
      "No se pudo conectar con el backend: " +
      error.message;
  }
}

function obtenerPoster(titulo) {
  const posters = {
    "interestelar": "interestelar.jpg",
    "el origen": "el-origen.jpg",
    "avatar: el camino del agua": "avatar-2.jpg",
    "spider-man: sin camino a casa": "spiderman.jpg",
    "coco": "coco.jpg",
    "intensamente 2": "intensamente-2.jpg",
    "duna: parte dos": "duna-2.jpg",
    "oppenheimer": "oppenheimer.jpg",
    "el conjuro": "el-conjuro.jpg",
    "jurassic world": "jurassic-world.jpg",
    "batman: el caballero de la noche": "batman.jpg",
    "super mario bros.: la película": "super-mario.jpg"
  };

  const nombre = titulo?.trim().toLowerCase();
  const archivo = posters[nombre];

  return archivo ? `img/peliculas/${archivo}` : "";
}


// 5. FUNCIONES DE UNA PELÍCULA


async function openMovie(movieId) {
  S.movie = S.movies.find((m) => id(m) === movieId);

  if (!S.movie) {
    toast("No se encontró la película.");
    return;
  }

  S.fn = null;
  S.seats = [];
  S.selected.clear();

  mostrarVista("reserva");
  $("bookingTitle").textContent = S.movie.titulo;

  
const poster = obtenerPoster(S.movie.titulo);

$("bookingPoster").src = poster;
$("bookingPoster").style.display = poster ? "block" : "none";
$("bookingPoster").alt = `Póster de ${S.movie.titulo}`;

  $("bookingMovie").innerHTML = `
    <p>
      ${esc(
        S.movie.sinopsis ||
        "Selecciona una función."
      )}
    </p>
  `;

  $("showtimeList").textContent = "Cargando...";
  $("seatMap").innerHTML = "";

  update();

  $("bookingSection").scrollIntoView({
    behavior: "smooth"
  });

  try {
    const data = await api(
      "/funciones/pelicula/" + movieId
    );

    S.functions = Array.isArray(data)
      ? data
      : data.funciones || [];

    
const disponibles = S.functions.filter((f) => {
  const estadoValido =
    !f.estado ||
    f.estado === "programada" ||
    f.estado === "activa";

  const fechaFuncion = new Date(f.fecha_hora);

  return estadoValido &&
    !isNaN(fechaFuncion.getTime()) &&
    fechaFuncion.getTime() > Date.now();
});

const claveFecha = (fecha) => {
  const d = new Date(fecha);

  const anio = d.getFullYear();
  const mes = String(d.getMonth() + 1).padStart(2, "0");
  const dia = String(d.getDate()).padStart(2, "0");

  return `${anio}-${mes}-${dia}`;
};

const dias = [...new Set(
  disponibles.map((f) => claveFecha(f.fecha_hora))
)].sort();

const selector = $("dateSelector");
const lista = $("showtimeList");

function mostrarFuncionesDelDia(diaSeleccionado) {
  selector.querySelectorAll(".date-option").forEach((btn) => {
    btn.classList.toggle(
      "active",
      btn.dataset.dia === diaSeleccionado
    );
  });

  const funcionesDelDia = disponibles.filter(
    (f) => claveFecha(f.fecha_hora) === diaSeleccionado
  );

  lista.innerHTML = funcionesDelDia.map((f) => `
    <button
      class="showtime"
      data-f="${esc(id(f))}"
    >
      <span>
        ${esc(date(f.fecha_hora))}
        <br>
        <small>
          ${esc(f.formato || "2D")} ·
          ${esc(f.idioma || "Español")}
        </small>
      </span>
      <b>${money(f.precio)}</b>
    </button>
  `).join("") || "No hay funciones para este día.";

  lista.querySelectorAll("[data-f]").forEach((btn) => {
    btn.onclick = () => chooseFunction(btn.dataset.f);
  });
}

selector.innerHTML = dias.map((dia) => {
  const fecha = new Date(`${dia}T12:00:00`);

  const etiqueta = fecha.toLocaleDateString("es-MX", {
    weekday: "short",
    day: "numeric",
    month: "short"
  });

  return `
    <button class="date-option" data-dia="${dia}">
      ${esc(etiqueta)}
    </button>
  `;
}).join("");

selector.querySelectorAll(".date-option").forEach((btn) => {
  btn.onclick = () => {
    S.fn = null;
    S.seats = [];
    S.selected.clear();
    $("seatMap").innerHTML = "";
    update();

    mostrarFuncionesDelDia(btn.dataset.dia);
  };
});

if (dias.length) {
  mostrarFuncionesDelDia(dias[0]);
} else {
  selector.innerHTML = "";
  lista.textContent = "No hay funciones programadas.";
}


  } catch (error) {
    $("showtimeList").textContent = error.message;
  }
}


// 6. ASIENTOS


async function chooseFunction(functionId) {
  S.fn = S.functions.find(
    (f) => id(f) === functionId
  );

  S.selected.clear();
  S.seats = [];

  document.querySelectorAll("[data-f]").forEach((btn) => {
    btn.classList.toggle(
      "active",
      btn.dataset.f === functionId
    );
  });

  update();

  $("seatMap").textContent = "Cargando asientos...";

  try {
    const data = await api(
      "/asientos/funcion/" + functionId
    );

    S.seats = data.asientos || [];

    const rows = {};

    S.seats.forEach((seat) => {
      if (!rows[seat.fila]) {
        rows[seat.fila] = [];
      }

      rows[seat.fila].push(seat);
    });

    $("seatMap").innerHTML = Object.values(rows)
      .map((row) => `
        <div class="seatrow">
          ${row.map((seat) => `
            <button
              class="seat ${
                seat.estado !== "disponible"
                  ? "occupied"
                  : ""
              }"
              data-s="${esc(seat.codigo)}"
              ${
                seat.estado !== "disponible"
                  ? "disabled"
                  : ""
              }
            >
              ${esc(seat.codigo)}
            </button>
          `).join("")}
        </div>
      `).join("");

    document.querySelectorAll("[data-s]").forEach((btn) => {
      btn.onclick = () => {
        const codigo = btn.dataset.s;

        if (S.selected.has(codigo)) {
          S.selected.delete(codigo);
        } else {
          S.selected.add(codigo);
        }

        btn.classList.toggle(
          "selected",
          S.selected.has(codigo)
        );

        update();
      };
    });

  } catch (error) {
    $("seatMap").textContent = error.message;
  }
}


// 7. RESUMEN DE SELECCIÓN


function update() {
  $("selectedSeats").textContent =
    [...S.selected].sort().join(", ") || "Ninguno";

  $("bookingTotal").textContent = money(
    S.selected.size * (S.fn?.precio || 0)
  );

  $("continuePurchase").disabled =
    !S.fn || !S.selected.size;
}


// 8. ABRIR CONFIRMACIÓN DE COMPRA


$("continuePurchase").onclick = () => {
  if (!S.token) {
    S.mode = "login";
    authSetup();

    $("authModal").classList.remove("hidden");
    return;
  }

  if (!S.fn || !S.selected.size) {
    toast("Selecciona una función y tus asientos.");
    return;
  }

  const funcion = S.fn;
  const seats = [...S.selected].sort();

  $("checkoutMessage").textContent = "";

  $("checkoutSummary").innerHTML = `
    <p>
      Película:
      <b>${esc(S.movie.titulo)}</b>
    </p>

    <p>
      Función:
      ${esc(date(funcion.fecha_hora))}
    </p>

    <p>
      Asientos:
      ${esc(seats.join(", "))}
    </p>

    <p>
      Total:
      <b>${money(seats.length * funcion.precio)}</b>
    </p>
  `;

  $("checkoutModal").classList.remove("hidden");
};


// 9. COMPRA + PAGO SIMULADO + BOLETOS


$("confirmPurchase").onclick = async () => {
  const button = $("confirmPurchase");
  const message = $("checkoutMessage");

  if (!S.fn || !S.selected.size) {
    message.textContent = "No hay asientos seleccionados.";
    return;
  }

  button.disabled = true;

  const functionId = id(S.fn);
  const selectedSeats = [...S.selected].sort();

  let compraId = "";
let etapa = "reservar";

try {
  // PASO 0: RESERVAR EN REDIS
  message.textContent = "Reservando asientos durante 10 minutos...";

  await api("/asientos/reservar", {
    method: "POST",
    body: JSON.stringify({
      funcion_id: functionId,
      asientos: selectedSeats
    })
  });

  // PASO 1: CREAR COMPRA
  etapa = "crear";
  message.textContent = "Creando compra...";

    const compra = await api("/compras/", {
      method: "POST",
      body: JSON.stringify({
        funcion_id: functionId,
        asientos: selectedSeats
      })
    });

    compraId = id(compra.compra || compra);

    if (!compraId) {
      throw new Error(
        "La compra se creó, pero el servidor no devolvió su ID. Revisa Mis compras antes de intentar otra vez."
      );
    }

    // PASO 2: PAGO SIMULADO
    etapa = "pagar";
    message.textContent = "Procesando pago simulado...";

    await api(`/compras/${compraId}/pagar`, {
      method: "POST"
    });

    // PASO 3: GENERAR BOLETOS
    etapa = "boletos";
    message.textContent = "Generando boletos...";

    const resultado = await api(
      `/boletos/generar/${compraId}`,
      {
        method: "POST"
      }
    );

    console.log("Boletos generados:", resultado);

    // PASO 4: CONFIRMAR EN PANTALLA
    message.textContent = "";

    $("checkoutModal").classList.add("hidden");

    toast("¡Pago realizado y boletos generados!");

    await chooseFunction(functionId);

    console.log("Compra completada:", compraId);

  } catch (error) {
    console.error(
      "Error en etapa:",
      etapa,
      error
    );

    if (compraId) {
      message.textContent =
        `La compra ${compraId} ya fue creada. ` +
        `Falló la etapa "${etapa}": ${error.message}. ` +
        "No vuelvas a comprar esos asientos. " +
        "Revisa Mis compras.";
    } else {
      message.textContent = error.message;
    }

  } finally {
    button.disabled = false;
  }
};


// 10. INTERFAZ DE AUTENTICACIÓN


function authUI() {
  $("authButton").textContent =
    S.token ? "Cerrar sesión" : "Iniciar sesión";

  $("userLabel").textContent =
    S.token ? "Sesión iniciada" : "";
}

function authSetup() {
  const register = S.mode === "register";

  $("authTitle").textContent =
    register ? "Crear cuenta" : "Iniciar sesión";

  $("nameField").classList.toggle(
    "hidden",
    !register
  );

  $("authName").required = register;

  document.querySelectorAll("[data-auth-tab]").forEach((btn) => {
    btn.classList.toggle(
      "active",
      btn.dataset.authTab === S.mode
    );
  });

  $("authSubmit").textContent =
    register ? "Registrarme" : "Entrar";
}


// 11. CAMBIAR ENTRE LOGIN Y REGISTRO


document.querySelectorAll("[data-auth-tab]").forEach((btn) => {
  btn.onclick = () => {
    S.mode = btn.dataset.authTab;
    authSetup();
  };
});


// 12. BOTÓN DE INICIAR / CERRAR SESIÓN


$("authButton").onclick = () => {
  if (S.token) {
    S.token = null;

    localStorage.removeItem("cinenow_token");

    authUI();
    toast("Sesión cerrada");

  } else {
    S.mode = "login";
    authSetup();

    $("authModal").classList.remove("hidden");
  }
};


// 13. REGISTRO E INICIO DE SESIÓN


$("authForm").onsubmit = async (event) => {
  event.preventDefault();

  const register = S.mode === "register";

  const body = {
    correo: $("authEmail").value,
    password: $("authPassword").value
  };

  if (register) {
    body.nombre = $("authName").value;
  }

  $("authMessage").textContent = "Procesando...";

  try {
    const data = await api(
      register
        ? "/usuarios/registro"
        : "/usuarios/login",
      {
        method: "POST",
        body: JSON.stringify(body)
      }
    );

    if (register) {
      $("authMessage").textContent =
        data.mensaje ||
        "Cuenta creada. Inicia sesión.";

      S.mode = "login";
      authSetup();

    } else {
      S.token = data.access_token || data.token;

      if (!S.token) {
        throw new Error(
          "No llegó el token de acceso."
        );
      }

      localStorage.setItem(
        "cinenow_token",
        S.token
      );

      authUI();

      $("authModal").classList.add("hidden");

      toast("¡Bienvenido!");
    }

  } catch (error) {
    $("authMessage").textContent = error.message;
  }
};


// 14. CONSULTAR MIS COMPRAS


async function purchases() {
  if (!S.token) {
    S.mode = "login";
    authSetup();

    $("authModal").classList.remove("hidden");
    return;
  }

  $("myPurchases").classList.remove("hidden");

  $("myPurchases").scrollIntoView({
    behavior: "smooth"
  });

  $("purchaseList").textContent = "Cargando...";

  try {
    const data = await api("/compras/mis-compras");

    const compras = Array.isArray(data)
      ? data
      : data.compras || [];

    if (!compras.length) {
      $("purchaseList").textContent =
        "Aún no tienes compras.";
      return;
    }

    $("purchaseList").innerHTML = compras.map((c) => `
      <div class="purchase">
        <b>Compra ${esc(id(c))}</b>

        <p>
          ${esc(date(c.creada_en || c.fecha))}
          ·
          ${esc((c.asientos || []).join(", "))}
        </p>

        <b>
          ${money(c.total)}
          ·
          ${esc(c.estado || "pendiente")}
        </b>
      </div>
    `).join("");

  } catch (error) {
    $("purchaseList").textContent = error.message;
  }
}

 
 // 15. CONSULTAR MIS BOLETOS
 


async function tickets() {
  if (!S.token) {
    S.mode = "login";
    authSetup();

    $("authModal").classList.remove("hidden");
    return;
  }

  const section = $("myTickets");
  const list = $("ticketList");

  section.classList.remove("hidden");

  section.scrollIntoView({
    behavior: "smooth"
  });

  list.textContent = "Cargando boletos...";

  try {
    const data = await api("/boletos/mis-boletos");

    const boletos = Array.isArray(data)
      ? data
      : data.boletos || [];

    if (!boletos.length) {
      list.textContent = "Todavía no tienes boletos.";
      return;
    }

    list.innerHTML = boletos.map((boleto) => {
      const pelicula = boleto.pelicula || "Película no disponible";
      const cine = boleto.cine || "Cine no disponible";
      const sala = boleto.sala || "Sala no disponible";
      const asiento = boleto.asiento || "No disponible";
      const codigo = boleto.codigo || "Sin código";
      const estado = boleto.estado || "No disponible";

      const fecha = boleto.fecha_hora
        ? date(boleto.fecha_hora)
        : "Fecha no disponible";

      const formato = boleto.formato || "No disponible";
      const idioma = boleto.idioma || "No disponible";

      return `
        <article class="ticket-card">

          <div class="ticket-header">
            <div>
              <span class="ticket-brand">CINENOW</span>
              <h3>${esc(pelicula)}</h3>
            </div>

            <span class="ticket-status">
              ${esc(estado)}
            </span>
          </div>

          <div class="ticket-details">

            <div>
              <small>CINE</small>
              <strong>${esc(cine)}</strong>
            </div>

            <div>
              <small>SALA</small>
              <strong>${esc(sala)}</strong>
            </div>

            <div>
              <small>FECHA Y HORA</small>
              <strong>${esc(fecha)}</strong>
            </div>

            <div>
              <small>ASIENTO</small>
              <strong>${esc(asiento)}</strong>
            </div>

            <div>
              <small>FORMATO</small>
              <strong>${esc(formato)}</strong>
            </div>

            <div>
              <small>IDIOMA</small>
              <strong>${esc(idioma)}</strong>
            </div>

          </div>

          <div class="ticket-footer">
            <small>CÓDIGO DE BOLETO</small>
            <strong>${esc(codigo)}</strong>
          </div>

        </article>
      `;
    }).join("");

  } catch (error) {
    list.textContent =
      "No se pudieron cargar los boletos: " +
      error.message;
  }
}



// 15. BOTONES DE NAVEGACIÓN

$("myTicketsLink").onclick = (event) => {
  event.preventDefault();
  tickets();
};

$("refreshTickets").onclick = tickets;

$("myPurchasesLink").onclick = (event) => {
  event.preventDefault();
  purchases();
};

$("refreshPurchases").onclick = purchases;

$("closeBooking").onclick = () => {
  S.fn = null;
  S.seats = [];
  S.selected.clear();

  mostrarVista("cartelera");
};

// Cerrar ventanas modales
document.querySelectorAll("[data-close]").forEach((btn) => {
  btn.onclick = () => {
    const modal = $(btn.dataset.close);

    if (modal) {
      modal.classList.add("hidden");
    }
  };
});


// 16. INICIAR APLICACIÓN


authUI();
movies();



function mostrarVista(vista) {
  const secciones = [
    "cartelera",
    "bookingSection",
    "myPurchases",
    "myTickets"
  ];

  secciones.forEach((seccion) => {
    document.getElementById(seccion)?.classList.add("hidden");
  });

  document.querySelector(".hero")?.classList.add("hidden");

  if (vista === "cartelera") {
    document.getElementById("cartelera").classList.remove("hidden");
    document.querySelector(".hero")?.classList.remove("hidden");
  }

  if (vista === "reserva") {
    document.getElementById("bookingSection").classList.remove("hidden");
  }

  if (vista === "compras") {
    document.getElementById("myPurchases").classList.remove("hidden");
  }

  if (vista === "boletos") {
    document.getElementById("myTickets").classList.remove("hidden");
  }

  window.scrollTo({ top: 0, behavior: "smooth" });
}


document.querySelector('a[href="#cartelera"]').addEventListener("click", (e) => {
  e.preventDefault();
  mostrarVista("cartelera");
});

document.getElementById("myPurchasesLink").addEventListener("click", (e) => {
  e.preventDefault();
  mostrarVista("compras");
});

document.getElementById("myTicketsLink").addEventListener("click", (e) => {
  e.preventDefault();
  mostrarVista("boletos");
});
