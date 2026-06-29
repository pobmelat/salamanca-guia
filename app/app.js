(() => {
  const D = window.GUIDE_DATA;
  const NS = "http://www.w3.org/2000/svg";
  const bounds = getBounds(D.route, D.stops);
  const map = document.querySelector("#route-map");
  const routeLayer = document.querySelector("#route-layer");
  const stopLayer = document.querySelector("#stop-layer");
  const userLayer = document.querySelector("#user-layer");
  const startBtn = document.querySelector("#start-btn");
  const centerBtn = document.querySelector("#center-btn");
  const gpsStatus = document.querySelector("#gps-status");
  const gpsDot = document.querySelector("#gps-dot");
  const nextStatus = document.querySelector("#next-status");
  const progress = document.querySelector("#progress");
  let watchId = null, userPos = null, active = false, currentStop = 0;
  const played = new Set(JSON.parse(localStorage.getItem("playedStops") || "[]"));

  function getBounds(route, stops){
    const all = [...route,...stops.map(s=>[s.lon,s.lat])];
    const xs=all.map(p=>p[0]), ys=all.map(p=>p[1]);
    return {minX:Math.min(...xs)-.0012,maxX:Math.max(...xs)+.0012,minY:Math.min(...ys)-.0009,maxY:Math.max(...ys)+.0009};
  }
  function project(lon,lat){return [55+(lon-bounds.minX)/(bounds.maxX-bounds.minX)*890,645-(lat-bounds.minY)/(bounds.maxY-bounds.minY)*590]}
  function el(name,attrs={}){const n=document.createElementNS(NS,name);Object.entries(attrs).forEach(([k,v])=>n.setAttribute(k,v));return n}
  const pts=D.route.map(p=>project(p[0],p[1])).map(p=>p.join(",")).join(" ");
  routeLayer.append(el("polyline",{points:pts,class:"route-shadow"}),el("polyline",{points:pts,class:"route-line"}));
  const kindColor={start:"#334f49",cafe:"#c4633b",monument:"#2e6a54",photo:"#c28b2c",finish:"#6a4777"};
  D.stops.forEach((s,i)=>{const [x,y]=project(s.lon,s.lat),g=el("g",{class:"marker",tabindex:"0","aria-label":`${s.time}, ${s.name}`});
    g.append(el("circle",{cx:x,cy:y,r:20,fill:kindColor[s.kind]}));const num=el("text",{x,y});num.textContent=s.id;g.append(num);
    const label=el("text",{x:x+27,y:y+(i===3||i===4?28:-24),class:"marker-label"});label.textContent=s.short;g.append(label);stopLayer.append(g)});

  const list=document.querySelector("#stops");
  D.stops.forEach((s,i)=>{const article=document.createElement("article");article.className="stop";article.dataset.index=i;
    const media=s.image?`<img src="${s.image}" alt="${s.name}" loading="lazy">`:`<div class="photo-fallback" aria-hidden="true">⌂</div>`;
    article.innerHTML=`${media}<div class="stop-body"><span class="stop-time">${s.time}</span><h2>${s.name}</h2><p>${s.desc}</p><button class="play" data-play="${i}">▶ Escuchar</button></div>`;list.append(article)});
  list.addEventListener("click",e=>{const b=e.target.closest("[data-play]");if(b){speechSynthesis.cancel();speak(+b.dataset.play,true)}});

  function distance(a,b){const R=6371000,p1=a.lat*Math.PI/180,p2=b.lat*Math.PI/180,dp=(b.lat-a.lat)*Math.PI/180,dl=(b.lon-a.lon)*Math.PI/180;const h=Math.sin(dp/2)**2+Math.cos(p1)*Math.cos(p2)*Math.sin(dl/2)**2;return 2*R*Math.asin(Math.sqrt(h))}
  function speak(i,manual=false){const s=D.stops[i];if(!manual&&played.has(s.id))return;const u=new SpeechSynthesisUtterance(s.speech);u.lang="es-ES";u.rate=.96;speechSynthesis.speak(u);played.add(s.id);localStorage.setItem("playedStops",JSON.stringify([...played]));}
  function updateCards(i){document.querySelectorAll(".stop").forEach((c,n)=>{c.classList.toggle("current",n===i);c.classList.toggle("passed",n<i)});currentStop=i;progress.style.width=`${i/(D.stops.length-1)*100}%`;nextStatus.textContent=i===D.stops.length-1?"Destino: Fonseca":`Siguiente: ${D.stops[i].short}`}
  function onPosition(pos){userPos={lat:pos.coords.latitude,lon:pos.coords.longitude,accuracy:pos.coords.accuracy};gpsStatus.textContent=`GPS activo · ±${Math.round(userPos.accuracy)} m`;gpsDot.classList.add("on");centerBtn.disabled=false;drawUser();
    let best=0,bestD=Infinity;D.stops.forEach((s,i)=>{const d=distance(userPos,s);if(d<bestD){bestD=d;best=i}});
    const upcoming=D.stops.findIndex((s,i)=>i>=currentStop&&distance(userPos,s)<D.meta.geofenceMeters);
    if(upcoming>=0){updateCards(upcoming);speak(upcoming)}else if(best>currentStop&&bestD<180)updateCards(best);
  }
  function drawUser(){userLayer.replaceChildren();if(!userPos)return;const [x,y]=project(userPos.lon,userPos.lat);const scale=890/(bounds.maxX-bounds.minX);const r=Math.min(90,Math.max(12,userPos.accuracy/85000*scale));userLayer.append(el("circle",{cx:x,cy:y,r,class:"accuracy"}),el("circle",{cx:x,cy:y,r:10,class:"user-dot"}))}
  function onError(err){gpsDot.classList.remove("on");gpsStatus.textContent=err.code===1?"Permiso de ubicación denegado":"No se pudo obtener la ubicación";document.querySelector("#hint").textContent="Puedes seguir usando el mapa y reproducir cada parada manualmente."}
  startBtn.addEventListener("click",()=>{speechSynthesis.cancel();const warm=new SpeechSynthesisUtterance("");warm.lang="es-ES";speechSynthesis.speak(warm);active=true;startBtn.textContent="Audioguía activada";startBtn.classList.add("active");if(!navigator.geolocation)return onError({code:0});watchId=navigator.geolocation.watchPosition(onPosition,onError,{enableHighAccuracy:true,maximumAge:5000,timeout:15000});});
  centerBtn.addEventListener("click",()=>{if(!userPos)return;map.scrollIntoView({behavior:"smooth",block:"center"});drawUser()});
  updateCards(0);
  if("serviceWorker" in navigator)window.addEventListener("load",()=>navigator.serviceWorker.register("sw.js"));
})();
