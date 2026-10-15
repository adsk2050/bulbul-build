import{a as d}from"./index-D74jF9BB.js";import{s as S,e as T,c as A}from"./StatsSheet-CtUsr3Xe.js";import{c as s,d as n,t as f,a as B,i as b,r as k,b as w,k as L,p,T as v,e as g,f as E,s as M}from"./Kit-F2FKtKBi.js";const P=[["Page","--c-page"],["Card top","--c-card-top"],["Card bottom","--c-card-bottom"],["Surface","--c-surface"],["Text primary","--c-text"],["Text secondary","--c-text-2"],["Text muted","--c-text-3"],["You / accent","--c-accent"],["CTA ledge","--c-cta-ledge"],["The Blast","--c-blast"],["Test Marathon","--c-marathon"],["Test Survival","--c-survival"],["Win","--c-win"],["Draw","--c-draw"],["Loss / danger","--c-loss"],["Gold","--c-gold"],["Share green","--c-share"]],x=[["k-t-num-xl","Satoshi Black 80"],["k-t-num","Satoshi Black 30"],["k-t-lead","Satoshi Bold 18"],["k-t-label","Satoshi Bold 14"],["k-t-overline","Satoshi Bold 11 caps"],["k-t-tag","Satoshi Bold 9 caps"],["k-t-body","Satoshi Medium 14"],["k-t-small","Satoshi Medium 12"],["k-t-title","Jaro 30"]],C=[{key:"classic",label:"The Blast"},{key:"survive",label:"Survival"},{key:"marathon",label:"Marathon"}],I=[{key:"best",label:"Top score"},{key:"runs",label:"Runs"},{key:"boundaries",label:"Boundaries"}];function o(t,l){return E(t,M(t,{runs:l,balls:l}))}const r=(t,l,a)=>`<section class="kg-section" id="kg-${t}"><h2 class="kg-head k-t-overline">${l}</h2>${a}</section>`;function N(){const t=P.map(([e,c])=>`<figure class="kg-swatch"><span style="background:var(${c})"></span><figcaption class="k-t-small">${e}<br><code>${c}</code></figcaption></figure>`).join(""),l=x.map(([e,c])=>`<p class="${e}">${c} · 158</p>`).join(""),a=[s({kind:"primary",label:"PLAY AGAIN",id:"kg-play-again"}),s({kind:"primary",label:"PLAY AGAIN",id:"kg-play-again-moving",moving:!0}),s({kind:"mode",label:"MODE"}),s({kind:"share",label:"Share on WhatsApp"}),s({kind:"challenge",label:"Challenge a friend"}),s({kind:"play-small",label:"PLAY"}),s({kind:"play-small",label:"PLAY",ink:"var(--c-marathon)"}),s({kind:"primary",label:"PLAY AGAIN",disabled:!0})].join(""),i=[s({kind:"primary",label:"PLAY",wide:!0}),s({kind:"secondary",label:"HOW TO PLAY"}),s({kind:"share-wide",label:"BRAG ABOUT MY STATS"})].join(""),h=`
    <div class="kg-row">${n({label:"The Blast",dot:"var(--c-blast)"})}${n({label:"The Blast",dot:"var(--c-blast)",state:"pressed"})}</div>
    <div class="kg-row">${n({label:"The Blast",dot:"var(--c-blast)",state:"focus"})}${n({label:"The Blast",dot:"var(--c-blast)",open:!0})}</div>
    <div class="kg-row">${n({label:"Test Marathon",dot:"var(--c-marathon)"})}${n({label:"Top score"})}</div>
    ${f(C,"classic","Mode")}
    ${B(I,"best","Rank by")}
    <div class="kg-row">${b({icon:"arrow-left",label:"Back"})}${b({icon:"volume",label:"Sound on"})}</div>`,u=`
    <div class="kg-card">${k({name:"Shashank",avatar:d(0),rank:2,first:!0})}</div>
    <div class="kg-card">${k({name:"Shashank",avatar:d(0),rank:2,best:"Best still stands  ·  158"})}</div>
    <div class="kg-card">${k({name:"Abhimanyu Rath",avatar:d(3),rank:12,best:"New best  ·  was 118"})}${w()}</div>
    ${L({key:"stamina-lofted-fielder-30"})}
    ${p({mode:"TEST MARATHON",label:"INNINGS"})}
    ${p({mode:"THE BLAST",label:"5 OVERS"})}`,m=v.map(e=>g(e.key,!0,e.short)).join("")+v.slice(1).map(e=>g(e.key,!1,e.short)).join(""),y=[o("classic",0),o("classic",2140),o("classic",16450),o("survive",420),o("marathon",9e3)].join(""),$=[0,2140,4800,16450].map(e=>{const c=S("classic",{...T(),runs:e,innings:e?20:0},{name:"Shashank",avatar:0});return A(c,e?{name:"Shashank",avatar:0}:null,!1)}).join("");return`<main class="kg" aria-label="UI kit">
    <h1 class="kg-title">FOUNDATIONS</h1>
    <p class="kg-note k-t-small">UI v1 · every part, every state · figures made up</p>
    ${r("colour","Colour",`<div class="kg-swatches">${t}</div>`)}
    ${r("type","Type",l)}
    ${r("ctas","CTAs",`<div class="kg-row kg-wrap">${a}</div><div class="kg-stack">${i}</div>`)}
    ${r("controls","Controls",h)}
    ${r("player","Player card, rank and key",u)}
    ${r("badges","Tier badges",`<div class="kg-row kg-wrap">${m}</div>`)}
    ${r("road","Road to Hitman",`<div class="kg-stack">${y}</div>`)}
    ${r("careers","Career cards",`<div class="kg-stack">${$}</div>`)}
  </main>`}function R(t){document.title="UI kit · Bulbul Flash Cricket",t.innerHTML=N(),t.addEventListener("click",l=>{const a=l.target.closest("button");a&&(a.classList.contains("k-pill")&&a.setAttribute("aria-expanded",String(a.getAttribute("aria-expanded")!=="true")),a.classList.contains("k-tab")&&a.parentElement?.querySelectorAll(".k-tab").forEach(i=>i.setAttribute("aria-selected",String(i===a))),a.classList.contains("k-chip")&&a.parentElement?.querySelectorAll(".k-chip").forEach(i=>i.setAttribute("aria-pressed",String(i===a))))})}export{N as galleryMarkup,R as kitGallery};
