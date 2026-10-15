import{L as re,aB as de,a as ue,r as c,s as ce}from"./index-14cqg0Ne.js";import{n as C,s as fe,o as pe,q as he,g as p,c as b,f as be}from"./Kit-W_TNwGGv.js";const ke=50,ye=200;function me(e){const s=[];let a=0;for(const n of e)a+=n.runs,n.isWicket&&(s.push(a),a=0);return s.push(a),s}function hs(e){const s=me(e.history);return{runs:e.runs,sixes:e.sixes,fours:e.fours,wickets:e.wickets,dots:e.dots,balls:e.balls,individual:Math.max(0,...s),hundreds:s.filter(a=>a>=U).length}}const U=100;function bs(){return{innings:0,runs:0,balls:0,sixes:0,fours:0,wickets:0,dots:0,highest:0,notOut:0,individual:0,hundreds:0}}function ks(){return{innings:0,runs:0,balls:0,sixes:0,fours:0,blows:0,wins:0,draws:0,losses:0}}function ys(){return{innings:0,runs:0,balls:0,fours:0,sixes:0,highest:0,individual:0,fifties:0,hundreds:0,doubles:0,longest:0}}function ve(e){return e.innings>0?Math.round(e.runs/e.innings*10)/10:0}function ge(e){return e.wins+e.draws}const we=20,$e=14,Se=14,Le=2**we-1,v=2**$e-1,N=2**Se,z=N-1;function Ae(e){return k(Math.floor((e-re)/864e5),0,z)}function Re(e,s,a){return(k(Math.floor(e),0,Le)*N+k(Math.floor(s),0,v))*N+(z-Ae(a))}function ms(e,s,a){return Re(e.primary(s),e.secondary(s),a)}function H(e){return v-k(Math.floor(e),0,v)}const vs=[{key:"runs",name:"Runs",blurb:"Every run scored in the Blast, added up. Level totals are split on who took fewer innings.",primary:e=>e.runs,secondary:e=>H(e.innings),figures:[{label:"runs",of:e=>e.runs},{label:"inns",of:e=>e.innings},{label:"6s",of:e=>e.sixes}],counts:e=>e.runs>0},{key:"boundaries",name:"Boundaries",blurb:"Most sixes, and fours where the sixes are level.",primary:e=>e.sixes,secondary:e=>k(e.fours,0,v),figures:[{label:"6s",of:e=>e.sixes},{label:"4s",of:e=>e.fours},{label:"inns",of:e=>e.innings}],counts:e=>e.sixes+e.fours>0},{key:"individual",name:"Individual",blurb:"The most one batsman has made. A wicket brings the next one in at nought, so this is not the same as a big total. Level scores are split on hundreds made.",primary:e=>e.individual??0,secondary:e=>k(e.hundreds??0,0,v),figures:[{label:"best",of:e=>e.individual??0},{label:"100s",of:e=>e.hundreds??0},{label:"inns",of:e=>e.innings}],counts:e=>(e.individual??0)>0}],gs=[{key:"balls",name:"Balls",blurb:"Every ball faced out there, added up. Level counts are split on who took fewer innings.",primary:e=>e.balls,secondary:e=>H(e.innings),figures:[{label:"balls",of:e=>e.balls},{label:"inns",of:e=>e.innings},{label:"runs",of:e=>e.runs}],counts:e=>e.balls>0},{key:"blows",name:"Blows",blurb:"Most blows taken and still come back. Level counts are split on balls faced.",primary:e=>e.blows,secondary:e=>k(e.balls,0,v),figures:[{label:"blows",of:e=>e.blows},{label:"balls",of:e=>e.balls},{label:"inns",of:e=>e.innings}],counts:e=>e.blows>0},{key:"runs",name:"Runs",blurb:"Every run made against the short stuff. Level totals are split on balls faced.",primary:e=>e.runs,secondary:e=>k(e.balls,0,v),figures:[{label:"runs",of:e=>e.runs},{label:"inns",of:e=>e.innings},{label:"won",of:e=>e.wins}],counts:e=>e.runs>0},{key:"boundaries",name:"Boundaries",blurb:"Most sixes, and fours where the sixes are level.",primary:e=>e.sixes,secondary:e=>k(e.fours,0,v),figures:[{label:"6s",of:e=>e.sixes},{label:"4s",of:e=>e.fours},{label:"inns",of:e=>e.innings}],counts:e=>e.sixes+e.fours>0}],ws=[{key:"runs",name:"Runs",blurb:"Every run scored in the Test Marathon, added up. Level totals are split on who took fewer innings.",primary:e=>e.runs,secondary:e=>H(e.innings),figures:[{label:"runs",of:e=>e.runs},{label:"inns",of:e=>e.innings},{label:"4s",of:e=>e.fours},{label:"6s",of:e=>e.sixes}],counts:e=>e.runs>0}];function k(e,s,a){return e<s?s:e>a?a:e}const E={width:362,height:214,radius:24},J=new URL(""+new URL("title-B9C_iBy6.webp",import.meta.url).href,import.meta.url).href,Q=new URL("data:image/svg+xml,%3csvg%20preserveAspectRatio='none'%20overflow='visible'%20style='display:%20block;'%20width='285.317'%20height='271.353'%20viewBox='0%200%20285.317%20271.353'%20fill='none'%20xmlns='http://www.w3.org/2000/svg'%3e%3cmask%20id='stroke0_0_29'%20fill='white'%3e%3cpath%20d='M142.658%200L179.689%2099.0319L285.317%20103.647L202.575%20169.468L230.826%20271.353L142.658%20213L54.4907%20271.353L82.7419%20169.468L0%20103.647L105.628%2099.0319L142.658%200Z'/%3e%3c/mask%3e%3cpath%20id='Star'%20d='M142.658%200L179.689%2099.0319L285.317%20103.647L202.575%20169.468L230.826%20271.353L142.658%20213L54.4907%20271.353L82.7419%20169.468L0%20103.647L105.628%2099.0319L142.658%200Z'%20stroke-width='54'%20stroke='url(%23paint0_linear_0_29)'%20stroke-opacity='0.07'%20mask='url(%23stroke0_0_29)'/%3e%3cdefs%3e%3clinearGradient%20id='paint0_linear_0_29'%20x1='136.465'%20y1='84.9575'%20x2='137.775'%20y2='242.631'%20gradientUnits='userSpaceOnUse'%3e%3cstop%20stop-color='white'/%3e%3cstop%20offset='1'%20stop-color='%23999999'%20stop-opacity='0'/%3e%3c/linearGradient%3e%3c/defs%3e%3c/svg%3e",import.meta.url).href,x=new URL(""+new URL("card-batsman-CASnDpF9.svg",import.meta.url).href,import.meta.url).href,Me="Satoshi, 'Segoe UI', Arial, sans-serif",m=(e,s)=>`${e} ${s}px ${Me}`,ee=e=>`400 ${e}px Jaro, Impact, sans-serif`,q=new Map;function M(e){let s=q.get(e);return s||(s=new Promise((a,n)=>{const t=new Image;t.onload=()=>a(t),t.onerror=()=>n(new Error(`Could not load ${e}`)),t.src=e}),q.set(e,s)),s}async function Te(){await Promise.all([document.fonts.load(ee(13),"A"),document.fonts.load(m(700,18),"A"),document.fonts.load(m(900,40),"0"),document.fonts.load(m(500,12),"a")]).catch(()=>{}),await Promise.all([J,Q,x].map(e=>M(e).catch(()=>null)))}const O=[[.1875,"#ffffff00"],[.46875,"#ffffff14"],[.5625,"#ffffff00"]],K={debutant:{stops:[[0,"#2b4c78"],[.55,"#1a3352"],[1,"#0f1f36"]],angle:135.6,edge:"#b9cde680",ink:"#f5efe6",quiet:"#a9bfd8",pill:"#5c83b540",pillInk:"#bfd3ec",ring:"#ffffff40",sheen:O},emerging:{stops:[[0,"#e8b98c"],[.28,"#b9784a"],[.5,"#f0c79e"],[.72,"#9a5a2f"],[1,"#c98b5a"]],angle:149.4,edge:"#ffe2c4",ink:"#2a1608",quiet:"#5a3218",pill:"#2a1608d9",pillInk:"#f0c79e",ring:"#2a160840",sheen:O},star:{stops:[[0,"#2a2e35"],[.45,"#121418"],[1,"#07080a"]],angle:149.4,edge:"#ffffff",ink:"#f5efe6",quiet:"#a9b2bc",pill:["#f6f8fa","#9aa3ac","#e3e8ed"],pillInk:"#111316",metal:["#ffffff","#b8c0c8","#f2f5f8"],ring:"#ffffff40",sheen:[[.1875,"#ffffff00"],[.46875,"#ffffff1f"],[.5625,"#ffffff00"]]},hitman:{stops:[[0,"#1c1608"],[.5,"#0a0805"],[1,"#050403"]],angle:149.4,edge:"#fff0b8",ink:"#f5efe6",quiet:"#bfa15a",pill:["#fff0b8","#c99a35","#f7d774"],pillInk:"#1a1204",metal:["#fff0b8","#e3b04b","#ffe08a"],ring:"#f3d27a",sheen:[[.1875,"#ffffff00"],[.45,"#ffe08a1a"],[.5,"#ff9cd012"],[.55,"#8fe3ff12"],[.6125,"#ffffff00"]]}},se={stops:[[0,"#7a1420"],[.52,"#4a0a13"],[1,"#22040a"]],angle:155,edge:"#d9a877",ink:"#fbf1e6",quiet:"#e0b4a4",pill:["#f0c79e","#b9784a","#e8b98c"],pillInk:"#2a1608",ring:"#d9a87780",sheen:O};function Ee(e,s){return s==="star"?e:s==="emerging"?se:{...e,stops:[[0,"#0b3a24"],[.55,"#052015"],[1,"#021009"]],angle:160,edge:s==="hitman"?"#f3d27a":"#3f7d5a",ink:"#f5efe6",quiet:"#b5c7bc",ring:"#ffffff40",pill:s==="hitman"?e.pill:"#ffffff1f",pillInk:s==="hitman"?e.pillInk:"#e7f0ea",metal:s==="hitman"?e.metal:void 0}}function Ce(e,s){const n=document.createElement("canvas");n.width=e*3,n.height=s*3;const t=n.getContext("2d");t.scale(3,3),t.strokeStyle="#ffffff0f",t.lineWidth=2.2,t.beginPath();for(let i=0;i<s+14;i+=14)for(let o=0;o<e+22;o+=22)t.moveTo(o+3,i+11),t.lineTo(o+11,i+4),t.lineTo(o+19,i+11);return t.stroke(),t.globalCompositeOperation="destination-in",t.fillStyle=Y(t,e,s,160,[[.1,"#000"],[.85,"#0000"]]),t.fillRect(0,0,e,s),n}function Y(e,s,a,n,t){const i=(n-90)*Math.PI/180,o=Math.abs(s/2*Math.cos(i))+Math.abs(a/2*Math.sin(i)),l=s/2,r=a/2,u=Math.cos(i)*o,h=Math.sin(i)*o,A=e.createLinearGradient(l-u,r-h,l+u,r+h);for(const[f,g]of t)A.addColorStop(f,g);return A}function $(e,s,a,n,t,i){e.beginPath(),e.moveTo(s+i,a),e.arcTo(s+n,a,s+n,a+t,i),e.arcTo(s+n,a+t,s,a+t,i),e.arcTo(s,a+t,s,a,i),e.arcTo(s,a,s+n,a,i),e.closePath()}function _(e,s,a,n,t){let i=a;for(const o of s)e.fillText(o,i,n),i+=e.measureText(o).width+t;return i-a-t}function Ie(e,s,a){return[...s].reduce((n,t)=>n+e.measureText(t).width+a,-a)}function j(e,s,a,n){const t=e.createLinearGradient(0,a,0,a+n);return t.addColorStop(0,s[0]),t.addColorStop(.5,s[1]),t.addColorStop(1,s[2]),t}async function Be(e,s,a,n,t){const i=s.tier.key,o=K[i]??K.debutant,l=s.mode==="marathon"?Ee(o,i):o,{width:r,height:u,radius:h}=E;if(e.save(),e.translate(n,t),e.save(),e.shadowColor="#0000008c",e.shadowBlur=32,e.shadowOffsetY=16,$(e,0,0,r,u,h),e.fillStyle="#000",e.fill(),e.restore(),e.save(),$(e,0,0,r,u,h),e.clip(),e.fillStyle=Y(e,r,u,l.angle,l.stops),e.fillRect(0,0,r,u),l===se){const d=e.createRadialGradient(r*.18,-u*.05,0,r*.18,-u*.05,r*.62);d.addColorStop(0,"#ff8a7a2e"),d.addColorStop(1,"#ff8a7a00"),e.fillStyle=d,e.fillRect(0,0,r,u),e.drawImage(Ce(r,u),0,0,r,u)}else if(s.mode==="marathon"&&i!=="star"){const d=e.createRadialGradient(r*.85,u*1.15,0,r*.85,u*1.15,r*.75);d.addColorStop(0,"#c8102e5c"),d.addColorStop(.62,"#c8102e00"),e.fillStyle=d,e.fillRect(0,0,r,u)}if(i==="emerging"&&s.mode!=="marathon")for(let d=0;d<u;d+=4)e.fillStyle=d/4%2?"#ffffff0f":"#3a1e0c0d",e.fillRect(0,d,r,1);else if(i==="debutant"&&s.mode!=="marathon"){e.save(),e.strokeStyle="#ffffff05",e.lineWidth=2;for(let d=-u;d<r;d+=9)e.beginPath(),e.moveTo(d,u),e.lineTo(d+u*.47,0),e.stroke();e.restore()}if(i==="star"){const d=await M(Q).catch(()=>null);d&&(e.save(),e.translate(134.5+142.66,-13+135.68),e.rotate(12*Math.PI/180),e.drawImage(d,-142.66,-135.68,285.3,271.35),e.restore())}else if(i==="hitman"){const d=await M(x).catch(()=>null);d&&e.drawImage(d,r*.5746,u*.1121,r*(1-.5746+.0207),u*(1-.1121+.4486))}const A=Y(e,r,u,135.4,l.sheen);e.fillStyle=A,e.fillRect(0,0,r,u),e.restore(),$(e,.75,.75,r-1.5,u-1.5,h),e.strokeStyle=l.edge,e.lineWidth=1.5,e.stroke(),i==="hitman"&&($(e,7,7,r-14,u-14,18),e.strokeStyle="#f3d27a47",e.lineWidth=1,e.stroke());const f=await M(J).catch(()=>null);if(f){const w=Math.min(70/f.width,25/f.height);e.drawImage(f,20,16+(25-f.height*w)/2,f.width*w,f.height*w)}e.font=ee(13);const g=s.tier.name,S=Ie(e,g,1.56)+20,R=21,T=r-20-S,G=18;if(Array.isArray(l.pill)){const d=e.createLinearGradient(T,0,T+S,0);d.addColorStop(0,l.pill[0]),d.addColorStop(.5,l.pill[1]),d.addColorStop(1,l.pill[2]),e.fillStyle=d}else e.fillStyle=l.pill;$(e,T,G,S,R,8),e.fill(),e.fillStyle=l.pillInk,e.textBaseline="middle",_(e,g,T+10,G+R/2+1,1.56);const L=i==="star"||i==="hitman"?66:82,y=44;if(e.save(),e.beginPath(),e.arc(20+y/2,L+y/2,y/2,0,Math.PI*2),e.closePath(),e.fillStyle=a?de(a.avatar):"#00000033",e.fill(),a){e.clip();const d=await M(ue(a.avatar)).catch(()=>null);d&&e.drawImage(d,20,L,y,y)}e.restore(),e.beginPath(),e.arc(20+y/2,L+y/2,y/2+1,0,Math.PI*2),e.strokeStyle=l.ring,e.lineWidth=2,e.stroke();const ne=a?.name??"Guest";e.font=m(700,18),e.textBaseline="alphabetic",e.fillStyle=l.metal?j(e,l.metal,L+6,20):l.ink,e.fillText(ne,76,L+22),e.font=m(700,9),e.fillStyle=l.quiet,_(e,`${s.modeName.toUpperCase()} · CAREER`,76,L+36,.9);const ie=s.ladder.measure.toLocaleString("en-US"),oe=s.mode==="survive"?"balls faced":`career ${C(s.mode)}`,F=i==="star"||i==="hitman",I=F?166:194;e.font=m(900,40),e.fillStyle=l.metal?j(e,l.metal,I-32,34):l.ink;const le=_(e,ie,20,I,-1.33);if(e.font=m(500,12),e.fillStyle=l.quiet,e.fillText(oe,20+le+8,I),F){const{progress:d,toNext:B,next:w}=s.ladder,P=184;e.fillStyle=i==="hitman"?"#f3d27a26":"#ffffff1f",$(e,20,P,150,4,2),e.fill(),e.fillStyle=i==="hitman"?"#f3d27a":"#dde3e8",$(e,20,P,Math.max(4,150*(w?d:1)),4,2),e.fill(),e.font=m(500,12),e.fillStyle=l.quiet,e.textAlign="right",e.fillText(w&&B!==null?`${B.toLocaleString("en-US")} ${C(s.mode)} to ${w.short}`:"Top of the game",r-20,P+6),e.textAlign="left"}e.restore()}const Pe=new URL(""+new URL("title-B9C_iBy6.webp",import.meta.url).href,import.meta.url).href,ae=new URL(""+new URL("cover-BiPAWP-p.webp",import.meta.url).href,import.meta.url).href,_e={width:1080,height:1920},Ue="Satoshi, 'Segoe UI', Arial, sans-serif",D=(e,s)=>`${e} ${s}px ${Ue}`,Ne=[[500,13],[600,10],[700,11],[800,22],[900,44]];let V=null;function Oe(){return V??=(async()=>{await Promise.all(Ne.map(([e,s])=>document.fonts.load(D(e,s),"0123456789"))),await Promise.all([Pe,ae].map(te))})().catch(()=>{}),V}const Z=new Map;function te(e){const s=Z.get(e);if(s)return s;const a=new Promise((n,t)=>{const i=new Image;i.onload=()=>n(i),i.onerror=()=>t(new Error(`Could not load ${e}`)),i.src=e});return Z.set(e,a),a}function Ye(e){return{hero:[{label:"Runs",value:e.runs},{label:"Highest",value:e.highest}],figures:[{label:"Hundreds",value:e.hundreds??0},{label:"Sixes",value:e.sixes},{label:"Fours",value:e.fours},{label:"Best ind.",value:e.individual??e.notOut},{label:"Balls",value:e.balls}]}}function De(e){return{hero:[{label:"Balls faced",value:e.balls},{label:"Survived",value:ge(e)}],figures:[{label:"Runs",value:e.runs},{label:"Blows",value:e.blows},{label:"Sixes",value:e.sixes},{label:"Fours",value:e.fours},{label:"Won",value:e.wins},{label:"Drawn",value:e.draws},{label:"Lost",value:e.losses}]}}function He(e){return{hero:[{label:"Highest",value:e.highest},{label:"Best ind.",value:e.individual}],figures:[{label:"Runs",value:e.runs},{label:"Per inns",value:ve(e)},{label:"Fifties",value:e.fifties},{label:"Hundreds",value:e.hundreds},{label:"Doubles",value:e.doubles},{label:"Longest",value:e.longest}]}}const We={classic:"Five overs. Three wickets. Beat my numbers.",survive:"Ten overs. One wicket. Last longer than me.",marathon:"Three batters. All day. Beat my total."},Ge={classic:"The Blast",survive:"Test Survival",marathon:"Test Marathon"};function $s(e,s,a,n=null){const t=e==="survive"?De(s):e==="marathon"?He(s):Ye(s),i=fe(e,s,a.granted??null);return{tier:{...i.tier,theme:he(e,i.tier)},ladder:i,nextLine:pe(e,i),mode:e,modeName:Ge[e],name:a.name||"You",avatar:a.avatar,innings:s.innings,standing:n,played:s.innings>0,...t}}const Fe={Runs:"Every run you have scored, added up across all your innings.",Highest:"Your biggest innings total, whatever it cost in wickets. 130 for two counts as 130.",Hundreds:`Times a batsman of yours got to ${U}. A wicket brings a new batsman in and the runs start again, so two down for twenty and 130 all told is a hundred — that batsman made 110.`,Sixes:"Every six you have hit, added up across all your innings.",Fours:"Every four you have hit, added up across all your innings.","Best ind.":"The most one batsman made, counted from the wicket before him rather than from the start of the innings.",Balls:"Every ball you have faced, added up across all your innings.","Balls faced":"Every ball you have faced out there, added up across all your innings.",Survived:"Innings you came through: the ones you won, plus the ones you drew.",Blows:"Bouncers that hit you. You take the blow and keep batting, and every one of them is counted.",Won:"Innings where you chased the hundred down before the overs ran out.",Drawn:"Innings where you batted out all ten overs without getting to a hundred. You survived, you just did not win.",Lost:"Innings where you lost your wicket before either of those happened.","Per inns":"Your runs divided by your innings. Not an average: a declared or retired batter is not out, so every innings counts once, however it ended.",Fifties:`Times one of your batters got to ${ke} without going on to ${U}.`,Doubles:`Times one of your batters got to ${ye}. Each is a hundred too.`,Longest:"Your longest innings, in balls faced by all three batters."};function qe(e){return Fe[e]??null}const Ke=(e,s="image/png",a)=>new Promise((n,t)=>e.toBlob(i=>i?n(i):t(new Error("Canvas gave back no image")),s,a));function je(e,s,a){const n=document.createElement("canvas");n.width=Math.round(e*a),n.height=Math.round(s*a);const t=n.getContext("2d");if(!t)throw new Error("No 2D canvas context");return t.scale(a,a),{canvas:n,ctx:t}}const Ve=e=>e.name&&e.name!=="You"?{name:e.name,avatar:e.avatar}:null;async function Ss(e,s,a=1){await Promise.all([Oe(),Te()]);const{width:n,height:t}=_e,{canvas:i,ctx:o}=je(n,t,a);o.fillStyle="#0a0b0d",o.fillRect(0,0,n,t);const l=await te(ae).catch(()=>null);if(l){const g=Math.max(n/l.width,t/l.height),S=l.width*g,R=l.height*g;o.drawImage(l,(n-S)/2,(t-R)/2,S,R)}const r=o.createLinearGradient(0,0,0,t);r.addColorStop(0,"#0a0b0d70"),r.addColorStop(.45,"#0a0b0dad"),r.addColorStop(1,"#0a0b0de8"),o.fillStyle=r,o.fillRect(0,0,n,t);const u=n*.86/E.width,h=E.height*u,f=Math.round((t-(h+150))/2);return o.save(),o.translate((n-E.width*u)/2,f),o.scale(u,u),await Be(o,e,Ve(e),0,0),o.restore(),o.textAlign="center",o.fillStyle="#f5efe6",o.font=D(700,34),o.globalAlpha=.92,o.fillText(s.replace(/^https?:\/\//,"").replace(/\/$/,""),n/2,f+h+96),o.globalAlpha=.66,o.font=D(500,26),o.fillText(We[e.mode],n/2,f+h+138),o.globalAlpha=1,Ke(i,"image/jpeg",.92)}const W='<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M15 7.5a4.5 4.5 0 1 0-4.24 4.49L9.5 13.25v2h-2v2h-2v2.5H2v-3.29l6.51-6.5A4.5 4.5 0 0 1 15 7.5Z" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/><circle cx="16.4" cy="7.1" r="1.35" fill="currentColor"/></svg>';function Ze(e){const s=e.state==="lost",a=e.state==="saved";return`
    <section class="key-pass k-ticket is-${e.state}" aria-labelledby="key-card-title">
      <div class="k-ticket-key">
        <div class="k-ticket-label k-t-overline">${p("key")}<span id="key-card-title">Career key</span>
          <button id="key-info" class="key-info" type="button" aria-label="What is a career key?"><span aria-hidden="true">i</span></button>
        </div>
        ${s?'<p class="key-line">No key on this phone. Make one: it is what brings this record back.</p>':`<p class="key-serial k-ticket-pill"><span>${c(e.code??"")}</span></p>`}
        ${a?'<button id="key-new" class="key-ghost" type="button">Make a new key</button>':""}
      </div>
      <span class="k-ticket-perf" aria-hidden="true"></span>
      <div class="k-ticket-save">${b({kind:"save",label:s?"MAKE IT":"SAVE",id:"key-save"})}</div>
    </section>`}function Ls(e){return`
    <section class="key-panel k-ticket" aria-labelledby="key-panel-title">
      <div class="k-ticket-key">
        <div class="k-ticket-label k-t-overline">${p("key")}<span id="key-panel-title">Career key</span></div>
        <p class="key-serial k-ticket-pill"><span>${c(e.code??"")}</span></p>
      </div>
      <span class="k-ticket-perf" aria-hidden="true"></span>
      <div class="k-ticket-save">${b({kind:"save",label:"SAVE",id:"key-panel-save"})}</div>
    </section>`}function As(){return`
    <section class="key-panel is-missing" aria-labelledby="key-missing-title">
      <div class="key-panel-face">
        <span class="key-mark" aria-hidden="true">${W}</span>
        <div class="key-panel-say">
          <h3 id="key-missing-title">No career key yet</h3>
          <p class="key-panel-line">It is what brings this record back on a new phone.</p>
        </div>
        <button id="key-missing-go" class="key-panel-key" type="button">MAKE IT</button>
      </div>
    </section>`}function Rs(){return`
    <button id="key-bar" class="key-bar" type="button">
      <span class="key-mark" aria-hidden="true">${W}</span>
      <span class="key-bar-say">Save your career key</span>
      <span class="key-bar-go">SAVE</span>
    </button>`}function Ms(e){return`
    <div class="key-toast" role="status">
      <div class="key-panel-face">
        <span class="key-mark" aria-hidden="true">${W}</span>
        <div class="key-panel-say">
          <h3>Your career key</h3>
          <p class="key-serial is-inline"><span>${c(e.code??"")}</span></p>
        </div>
        <button id="key-toast-save" class="key-panel-key" type="button">SAVE</button>
        <button id="key-toast-close" class="key-toast-close" type="button" aria-label="Close">
          <span aria-hidden="true">&times;</span>
        </button>
      </div>
    </div>`}function Ts(e){return`
    <div class="key-modal" role="dialog" aria-modal="true" aria-labelledby="key-modal-title">
      <div class="key-sheet ks-sheet">
        <i class="ks-grab" aria-hidden="true"></i>
        <div class="ks-head">
          <span class="ks-mark" aria-hidden="true">${p("key")}</span>
          <h2 id="key-modal-title" class="ks-title">SAVE YOUR CAREER KEY</h2>
          <button id="key-modal-close" class="ks-close" type="button" aria-label="Close">${p("close")}</button>
        </div>
        <p class="key-serial ks-key"><span>${c(e.code??"")}</span></p>
        <p class="ks-say">This and your name bring your record back: every run, every innings, your tier and your place on the board. Without it, a new phone or a cleared browser starts you at nought.</p>
        <p class="key-hero ks-hint">${p("scan")}<span><b>Screenshot this screen</b><small>The surest way to keep it. Your phone already knows how.</small></span></p>
        ${b({kind:"primary",label:"SAVE AS IMAGE",id:"key-image",wide:!0})}
        <div class="ks-more">
          ${b({kind:"share-wide",label:"WHATSAPP",id:"key-whatsapp"})}
          ${b({kind:"secondary",label:"COPY",id:"key-copy"})}
        </div>
        <p id="key-trouble" class="key-trouble hidden" role="alert"></p>
        <p class="ks-fine">Put it somewhere you’ll still have in a year. A copied key lasts until the next thing you copy; a picture outlives both.</p>
      </div>
    </div>`}function Es(e=null){return`
    <div class="key-modal" role="dialog" aria-modal="true" aria-labelledby="key-about-title">
      <div class="key-sheet ks-sheet">
        <i class="ks-grab" aria-hidden="true"></i>
        <div class="ks-head">
          <span class="ks-mark" aria-hidden="true">${p("key")}</span>
          <h2 id="key-about-title" class="ks-title">WHAT IS A CAREER KEY?</h2>
          <button class="ks-close" type="button" data-close aria-label="Close">${p("close")}</button>
        </div>
        <p class="ks-say is-lead">This game has no accounts. Who you are is kept by your browser, and browsers forget: after a week away, on a new phone, or the moment somebody clears their history.</p>
        <div class="ks-example">
          <span class="k-t-overline">Three words and two numbers</span>
          <p class="key-serial ks-key is-small"><span>${c(e??"stamina-lofted-fielder-30")}</span></p>
          <p class="ks-say">Type it with the name you bat under and your whole record comes back.</p>
        </div>
        <p class="ks-safe"><span aria-hidden="true">${Xe}</span>It only works with your name, so a key on its own is no use to anybody who finds it.</p>
        ${b({kind:"primary",label:"GOT IT",id:"key-about-close",wide:!0})}
      </div>
    </div>`}const Xe='<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 3 4.5 6v5.5c0 4.4 3.1 8.2 7.5 9.5 4.4-1.3 7.5-5.1 7.5-9.5V6L12 3Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="m8.8 12.2 2.2 2.2 4.2-4.4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>';function Cs(e){const{name:s="",local:a=null,sending:n=!1,error:t=null,done:i=null}=e;return i?ze(i):`
    <div class="key-modal" role="dialog" aria-modal="true" aria-labelledby="restore-title">
      <div class="key-sheet restore-sheet ks-sheet">
        <i class="ks-grab" aria-hidden="true"></i>
        <form id="restore-form" class="rs-form">
          <div class="ks-head">
            <span class="ks-mark" aria-hidden="true">${p("key")}</span>
            <h2 id="restore-title" class="ks-title">BRING YOUR RECORD BACK</h2>
            <button id="restore-close" class="ks-close" type="button" aria-label="Close">${p("close")}</button>
          </div>
          <p class="ks-say">Your name and your career key, together. Paste the key in whole: three words and two numbers.</p>
          <label class="restore-field rs-field"><span>The name you bat under</span>
            <input id="restore-name" type="text" maxlength="14" autocomplete="nickname"
              enterkeyhint="next" placeholder="Up to 14 characters" value="${c(s)}" required>
          </label>
          <label class="restore-field rs-field${t?" is-wrong":""}"><span>Your career key</span>
            <input id="restore-key" type="text" autocomplete="off" autocapitalize="none"
              autocorrect="off" spellcheck="false" enterkeyhint="done"
              placeholder="yorker-sprint-cover-47" required${t?' aria-invalid="true" aria-describedby="restore-error"':""}>
          </label>
          ${t?`<p id="restore-error" class="claim-error rs-error" role="alert">${c(t)}</p>`:""}
          ${a?Je(a):""}
          <button id="restore-send" type="submit" class="k-cta k-cta--primary is-wide"${n?" disabled":""}><span class="k-cta-face"><span>${n?"CHECKING…":"BRING IT BACK"}</span></span></button>
        </form>
      </div>
    </div>`}function ze(e){return`
    <div class="key-modal" role="dialog" aria-modal="true" aria-labelledby="restore-done-title">
      <div class="key-sheet restore-sheet ks-sheet is-done">
        <i class="ks-grab" aria-hidden="true"></i>
        <div class="ks-head">
          <span class="ks-mark" aria-hidden="true">${p("key")}</span>
          <h2 id="restore-done-title" class="ks-title">WELCOME BACK, ${c(e.name.toUpperCase())}</h2>
        </div>
        <p class="ks-say is-lead">Your record is yours again: every innings, every run, your tier and your place on the board.</p>
        ${b({kind:"primary",label:"SEE MY RECORD",id:"restore-done",wide:!0})}
      </div>
    </div>`}function Je(e){const s=`${e.innings} innings`,a=`${e.runs} ${e.runs===1?"run":"runs"}`;return`
          <div class="restore-losing">
            <p class="restore-losing-say">This phone has <b>${s}</b> and <b>${a}</b> on it,
              counted nowhere yet. Bringing your record back replaces them.</p>
          </div>`}function Is(e="restore-panel"){return`
    <section class="key-panel restore-panel" aria-labelledby="${c(e)}-title">
      <div class="key-panel-face">
        <span class="key-mark" aria-hidden="true">${xe}</span>
        <div class="key-panel-say">
          <h3 id="${c(e)}-title">Played before?</h3>
          <p class="restore-panel-line">Bring your record back</p>
        </div>
        <button id="${c(e)}-go" class="key-panel-key" type="button">RESTORE</button>
        <button id="${c(e)}-close" class="key-toast-close" type="button" aria-label="No thanks">
          <span aria-hidden="true">&times;</span>
        </button>
      </div>
    </section>`}function Qe(e,s){return`<button id="${c(e)}" class="restore-link" type="button">${c(s)}</button>`}const Bs="Is that you? Bring your record back",xe='<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M15 7.5a4.5 4.5 0 1 0-4.24 4.49L9.5 13.25v2h-2v2h-2v2.5H2v-3.29l6.51-6.5A4.5 4.5 0 0 1 15 7.5Z" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round"/><circle cx="16.4" cy="7.1" r="1.35" fill="currentColor"/></svg>';function es(e,s="YOUR RECORD",a=""){const n=(i,o,l)=>`<span class="rival-record-cell ${l}"><b>${i}</b><i>${o}</i></span>`,t=e.won+e.lost+e.drawn;return`<section class="rival-record${a?` ${a}`:""}" aria-label="${s.toLowerCase()}: ${e.won} won, ${e.lost} lost, ${e.drawn} drawn">
    <h3 class="rival-section-head">${s}<small>${t} match${t===1?"":"es"}</small></h3>
    <div class="rival-record-row">
      ${n(e.won,"Won","is-won")}${n(e.lost,"Lost","is-lost")}${n(e.drawn,"Drawn","is-drawn")}
    </div>
  </section>`}function Ps(e,s=[]){const a=(o,l,r)=>`<span class="rv-n ${r}"><b>${o}</b><i>${l}</i></span>`,n=Array.from({length:4},(o,l)=>s[l]?`<i class="rv-chip is-${s[l]}">${s[l]}</i>`:'<i class="rv-chip is-empty"></i>').join(""),i=e.won+e.lost?`<i class="is-won" style="flex:${e.won}"></i><i class="is-lost" style="flex:${e.lost}"></i>`:'<i class="is-none" style="flex:1"></i>';return`<section class="rival-record rv-record" aria-label="Your record: ${e.won} won, ${e.lost} lost, ${e.drawn} drawn">
    <div class="rv-scoreline">
      <div class="rv-score">${a(e.won,"WON","is-won")}${a(e.lost,"LOST","is-lost")}${a(e.drawn,"DRAWN","is-drawn")}</div>
      <div class="rv-form"><span>${s.length?`LAST ${s.length}`:"FORM"}</span><span class="rv-chips">${n}</span></div>
    </div>
    <div class="rv-share" aria-hidden="true">${i}</div>
  </section>`}const ss={classic:"Blast",survive:"Survival",marathon:"Marathon"},as=new URL(""+new URL("title-B9C_iBy6.webp",import.meta.url).href,import.meta.url).href,ts=new URL("data:image/svg+xml,%3csvg%20preserveAspectRatio='none'%20overflow='visible'%20style='display:%20block;'%20width='285.317'%20height='271.353'%20viewBox='0%200%20285.317%20271.353'%20fill='none'%20xmlns='http://www.w3.org/2000/svg'%3e%3cmask%20id='stroke0_0_29'%20fill='white'%3e%3cpath%20d='M142.658%200L179.689%2099.0319L285.317%20103.647L202.575%20169.468L230.826%20271.353L142.658%20213L54.4907%20271.353L82.7419%20169.468L0%20103.647L105.628%2099.0319L142.658%200Z'/%3e%3c/mask%3e%3cpath%20id='Star'%20d='M142.658%200L179.689%2099.0319L285.317%20103.647L202.575%20169.468L230.826%20271.353L142.658%20213L54.4907%20271.353L82.7419%20169.468L0%20103.647L105.628%2099.0319L142.658%200Z'%20stroke-width='54'%20stroke='url(%23paint0_linear_0_29)'%20stroke-opacity='0.07'%20mask='url(%23stroke0_0_29)'/%3e%3cdefs%3e%3clinearGradient%20id='paint0_linear_0_29'%20x1='136.465'%20y1='84.9575'%20x2='137.775'%20y2='242.631'%20gradientUnits='userSpaceOnUse'%3e%3cstop%20stop-color='white'/%3e%3cstop%20offset='1'%20stop-color='%23999999'%20stop-opacity='0'/%3e%3c/linearGradient%3e%3c/defs%3e%3c/svg%3e",import.meta.url).href,ns=new URL(""+new URL("card-batsman-CASnDpF9.svg",import.meta.url).href,import.meta.url).href,is='<svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M4 20h4L19 9l-4-4L4 16v4Z" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/><path d="m13.5 6.5 4 4" stroke="currentColor" stroke-width="1.8"/></svg>';function _s(e){const{cards:s,at:a=0,where:n="page"}=e,t=s.length>1,i=s.some(o=>o.facts.played);return`
    <div class="stats-sheet-inner st-page is-${n}" role="document">
      <header class="st-head">${n==="page"?`
        <button id="stats-back" class="k-icon-button" type="button" aria-label="Back">${p("arrow-left")}</button>`:""}
        <h2 class="st-title">MY STATS</h2>
        ${t?os(s,a):""}
      </header>
      <div id="stats-rail" class="stats-stage${t?" is-rail":""}"${t?' role="group" aria-label="Your careers, one a mode"':""}>${s.map((o,l)=>ls(o,e.who??null,l===0,l===a)).join("")}</div>
      ${e.careerKey?Ze(e.careerKey):""}
      ${e.rivals&&e.rivals.won+e.rivals.lost+e.rivals.drawn>0?es(e.rivals,"RIVALS RECORD","is-stats"):""}
      ${e.offerRestore?`<p class="stats-note">Played before? ${Qe("stats-restore","Bring your record back")}</p>`:""}
      <p id="stats-status" class="stats-status hidden" role="status" aria-live="polite"></p>
      <div id="stats-toast" class="stats-toast" role="status" aria-live="polite"></div>
      <div class="st-foot">${i?b({kind:"share-wide",label:"SHARE MY CARD",id:"stats-brag"}):b({kind:"primary",label:"PLAY YOUR FIRST INNINGS",id:"stats-play",wide:!0})}</div>
    </div>`}function os(e,s){return`<div class="st-switch stats-dots" role="tablist" aria-label="Which mode">${e.map((a,n)=>`
          <button class="stats-dot${n===s?" is-on":""}" type="button" role="tab" data-slide="${n}" aria-selected="${n===s}"
            aria-label="${c(a.facts.modeName)}"><span>${c(ss[a.facts.mode]??a.facts.modeName)}</span></button>`).join("")}
        </div>`}function ls(e,s,a,n){const{facts:t}=e;return`
      <div class="stats-slide" data-mode="${c(t.mode)}" role="group" aria-label="${c(t.modeName)}"${n?' data-live="1"':""}>
        ${rs(t,s,a)}
        ${be(t.mode,t.ladder)}
        ${us(e)}
      </div>`}function rs(e,s,a=!0){const n=e.tier.key,t=s?ce(s.avatar,s.name):'<span class="board-kit is-empty" aria-hidden="true"></span>',i=s?`<button${a?' id="stats-edit"':""} class="st-edit" type="button" aria-label="Edit your name, kit and batting hand">${is}</button>`:"",o=e.ladder.measure.toLocaleString("en-US"),l=e.mode==="survive"?"balls faced":`career ${C(e.mode)}`;return`<article class="st-card tier-${c(n)} is-${c(e.mode)}" aria-label="${c(`${s?.name??"Guest"}, ${e.tier.name}, ${e.modeName}: ${o} ${l}`)}">
          <i class="st-card-grain" aria-hidden="true"></i>${n==="star"?`<img class="st-card-star" src="${ts}" alt="" aria-hidden="true">`:""}${n==="hitman"?`<img class="st-card-batsman" src="${ns}" alt="" aria-hidden="true"><i class="st-card-rim" aria-hidden="true"></i>`:""}<i class="st-card-sheen" aria-hidden="true"></i>
          <div class="st-card-top"><img class="st-card-logo" src="${as}" alt="" decoding="async"><span class="st-card-tier">${c(e.tier.name)}</span></div>
          <div class="st-card-who">${t}<span class="st-card-name"><b>${c(s?.name??"Guest")}</b><small>${c(e.modeName.toUpperCase())} &middot; CAREER</small></span>${i}</div>
          <div class="st-card-foot"><div class="st-card-figure"><b>${o}</b><span>${l}</span></div>${n==="star"||n==="hitman"?cs(e):""}</div>
        </article>`}const X={classic:["Innings","Sixes","Highest","Fours","Balls","Best rank"],survive:["Innings","Survived","Won","Runs","Blows","Best rank"],marathon:["Innings","Highest","Best ind.","Hundreds","Fifties","Best rank"]},ds=new Set(["Highest","Best ind.","Best rank"]);function us(e){const{facts:s}=e,a=new Map([...s.hero,...s.figures].map(t=>[t.label,t.value])),n=t=>{if(t==="Innings")return s.innings.toLocaleString("en-US");if(t==="Best rank")return e.rank?`#${e.rank}`:"—";const i=a.get(t);return i===void 0||!s.played&&ds.has(t)?"—":typeof i=="number"?i.toLocaleString("en-US"):String(i)};return`<div class="st-tiles">${(X[s.mode]??X.classic).map(t=>{const i=qe(t),o=i?"button":"div";return`<${o} class="st-tile${t==="Best rank"&&e.rank?" is-rank":""}"${i?` type="button" data-stat="${c(t)}"`:""}>
          <b>${c(n(t))}</b><span>${c(t)}</span></${o}>`}).join("")}</div>`}function cs(e){const{progress:s,toNext:a,next:n}=e.ladder;return!n||a===null?'<div class="st-card-progress"><span class="st-card-track"><i style="width:100%"></i></span><small>Top of the game</small></div>':`<div class="st-card-progress"><span class="st-card-track"><i style="width:${Math.round(s*100)}%"></i></span>
          <small>${a.toLocaleString("en-US")} ${C(e.mode)} to ${c(n.short)}</small></div>`}export{vs as B,ws as M,Bs as R,gs as S,W as a,_s as b,rs as c,Ss as d,bs as e,Cs as f,Ls as g,As as h,Is as i,Rs as j,Ms as k,Es as l,Ts as m,Ps as n,qe as o,ks as p,ys as q,Qe as r,$s as s,ms as t,hs as u};
