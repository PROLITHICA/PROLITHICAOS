import { Component, inject, signal, OnDestroy } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DatePipe } from '@angular/common';
import { ApiService } from '../../core/api.service';
@Component({selector:'app-chat',standalone:true,imports:[FormsModule,DatePipe],templateUrl:'./chat.component.html'})
export class ChatComponent implements OnDestroy{
 api=inject(ApiService); threads=signal<any[]>([]);people=signal<any[]>([]);messages=signal<any[]>([]);selected=signal<any>(null);error=signal('');busy=signal(false);ready=signal(false);
 draft='';name='';members:string[]=[];direct=true; groupMembers:string[]=[];groupName='';
 timer=window.setInterval(()=>{this.load();if(this.selected())this.read(this.selected().id);},8000);
 constructor(){this.load();} ngOnDestroy(){clearInterval(this.timer);}
 fail(e:any){this.busy.set(false);this.error.set(e.error?.detail || JSON.stringify(e.error || 'Unable to connect. Please try again.'));}
 load(){this.api.get<any>('/workspace/threads/').subscribe({next:d=>{this.threads.set(d.threads);this.people.set(d.people);this.ready.set(true);},error:e=>this.fail(e)});}
 select(t:any){this.groupName=t.name;this.groupMembers=t.members.filter((m:any)=>!m.admin).map((m:any)=>m.id);this.selected.set(t);this.messages.set([]);this.error.set('');this.read(t.id);}
 read(id:string){this.api.get<any[]>('/workspace/threads/'+id+'/messages/').subscribe({next:m=>{if(this.selected()?.id===id)this.messages.set(m);},error:e=>this.fail(e)});}
 create(){if(this.busy())return;this.busy.set(true);this.error.set('');this.api.post<any>('/workspace/threads/',{name:this.name,members:this.members,direct:this.direct}).subscribe({next:r=>{this.busy.set(false);this.api.get<any>('/workspace/threads/').subscribe({next:d=>{this.threads.set(d.threads);this.select(d.threads.find((t:any)=>t.id===r.id));},error:e=>this.fail(e)});this.name='';this.members=[];},error:e=>this.fail(e)});}
 manage(){if(this.busy())return;this.busy.set(true);const id=this.selected().id;this.api.patch('/workspace/threads/'+id+'/messages/',{name:this.groupName,members:this.groupMembers}).subscribe({next:()=>{this.busy.set(false);this.api.get<any>('/workspace/threads/').subscribe({next:d=>{this.threads.set(d.threads);this.select(d.threads.find((t:any)=>t.id===id));},error:e=>this.fail(e)});},error:e=>this.fail(e)});}
 send(){if(this.busy()||!this.draft.trim())return;const id=this.selected().id;this.busy.set(true);this.error.set('');this.api.post('/workspace/threads/'+id+'/messages/',{body:this.draft}).subscribe({next:()=>{this.busy.set(false);this.draft='';this.read(id);},error:e=>this.fail(e)});}
}
