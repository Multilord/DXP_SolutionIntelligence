import React, { useEffect, useState } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import * as Tooltip from '@radix-ui/react-tooltip';
import { Command } from 'cmdk';
import { motion, useReducedMotion } from 'motion/react';
import { ArrowRight, BookOpen, Database, FileText, Layers3, Search, Sparkles, X, GitBranch, CircleHelp, ListChecks, Command as CommandIcon } from 'lucide-react';

type Row = Record<string, any>;
export function Hint({ text, children }: {text:string;children:React.ReactNode}) {
  return <Tooltip.Provider delayDuration={250}><Tooltip.Root><Tooltip.Trigger asChild>{children}</Tooltip.Trigger><Tooltip.Portal><Tooltip.Content className="atlas-tooltip" sideOffset={8}>{text}<Tooltip.Arrow/></Tooltip.Content></Tooltip.Portal></Tooltip.Root></Tooltip.Provider>;
}

export function CommandSearch({incidents,documents,onIncident,onDocument,onNavigate,disabled=false}:{incidents:Row[];documents:Row[];onIncident:(id:string)=>void;onDocument:(id:string)=>void;onNavigate:(id:string)=>void;disabled?:boolean}) {
  const [open,setOpen]=useState(false);
  useEffect(()=>{const listener=(e:KeyboardEvent)=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'&&!disabled){e.preventDefault();setOpen(v=>!v);}};document.addEventListener('keydown',listener);return()=>document.removeEventListener('keydown',listener);},[disabled]);
  const select=(action:()=>void)=>{setOpen(false);action();};
  const pages=[['workspace','Incident workspace',Layers3],['library','Solution library',BookOpen],['sources','Knowledge sources',Database],['timeline','System timeline',GitBranch],['gaps','Knowledge gaps',CircleHelp],['review','Review queue',ListChecks]] as const;
  return <Dialog.Root open={open} onOpenChange={setOpen}>
    <Dialog.Trigger asChild><button className="global-search" disabled={disabled}><Search size={16}/><span>Search anything…</span><kbd>Ctrl K</kbd></button></Dialog.Trigger>
    <Dialog.Portal><Dialog.Overlay className="command-overlay"/><Dialog.Content className="command-dialog"><Dialog.Title className="sr-only">Search your workspace</Dialog.Title><Dialog.Description className="sr-only">Find an incident, source document, or workspace page. Use arrow keys to move and Enter to open.</Dialog.Description>
      <Command label="Workspace search"><div className="command-input-wrap"><Search size={21}/><Command.Input placeholder="Search incidents, evidence, pages…" autoFocus/><Dialog.Close className="icon-button" aria-label="Close search"><X size={17}/></Dialog.Close></div><Command.List><Command.Empty>No matches. Try an incident ID or source title.</Command.Empty>
        <Command.Group heading="Navigate">{pages.map(([id,title,Icon])=><Command.Item key={id} value={'page '+title} onSelect={()=>select(()=>onNavigate(id))}><Icon size={17}/><span>{title}</span><ArrowRight size={14}/></Command.Item>)}</Command.Group>
        <Command.Group heading="Incidents">{incidents.map(i=><Command.Item key={i.id} value={i.id+' '+i.title} onSelect={()=>select(()=>onIncident(i.id))}><Layers3 size={17}/><span>{i.title}<small>{i.id} · {i.component}</small></span><ArrowRight size={14}/></Command.Item>)}</Command.Group>
        <Command.Group heading="Knowledge sources">{documents.map(d=><Command.Item key={d.id} value={d.id+' '+d.title} onSelect={()=>select(()=>onDocument(d.id))}><FileText size={17}/><span>{d.title}<small>{d.source_type} · {d.id}</small></span><ArrowRight size={14}/></Command.Item>)}</Command.Group>
      </Command.List><div className="command-footer"><span><kbd>↑</kbd><kbd>↓</kbd> Navigate</span><span><kbd>↵</kbd> Open</span><span><kbd>esc</kbd> Close</span><CommandIcon size={14}/></div></Command>
    </Dialog.Content></Dialog.Portal>
  </Dialog.Root>;
}

export function IntelligenceHero({documents,procedures,onBrowse}:{documents:number;procedures:number;onBrowse:()=>void}) {
  const reduced=useReducedMotion();
  return <motion.section className="intelligence-hero" initial={reduced?false:{opacity:0,y:10}} animate={{opacity:1,y:0}} transition={{duration:.3}}>
    <div className="hero-copy"><span className="hero-kicker"><span/> KNOWLEDGE, CONNECTED</span><h2>The right fix.<br/><span>The full picture.</span></h2><p>Turn collective experience into your next resolution.<br/>Find the evidence. Check the context. Move forward.</p><button onClick={onBrowse}>Explore solution library<ArrowRight size={16}/></button></div>
    <div className="knowledge-map" aria-label={`${documents} knowledge sources connected to ${procedures} reviewed solutions`}><svg className="map-lines" viewBox="0 0 360 200" aria-hidden="true"><path d="M65 40 C130 40 110 100 180 100 S240 40 295 40 M65 160 C130 160 110 100 180 100 S240 160 295 160"/><path d="M65 40V160 M295 40V160"/></svg><span className="map-node node-kb"><BookOpen size={16}/>Internal KB</span><span className="map-node node-ticket"><Layers3 size={16}/>Past tickets</span><span className="map-node node-sap"><Database size={16}/>SAP references</span><span className="map-node node-share"><FileText size={16}/>SharePoint</span><div className="map-center"><Sparkles size={27}/><span>atlas intelligence</span></div><div className="map-caption">{documents} sources <span>·</span> {procedures} reviewed solutions</div></div>
  </motion.section>;
}

export function AnimatedMetric({label,value,note,icon}:{label:string;value:number;note:string;icon:React.ReactNode}) {
  const reduced=useReducedMotion();
  return <motion.div className="metric" initial={reduced?false:{opacity:0,y:8}} animate={{opacity:1,y:0}} transition={{duration:.25}}><div><p>{label}</p><span className="metric-icon">{icon}</span></div><strong>{String(value).padStart(2,'0')}</strong><span>{note}</span></motion.div>;
}
