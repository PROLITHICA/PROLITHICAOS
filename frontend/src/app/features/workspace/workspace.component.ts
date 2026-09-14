import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { DatePipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { ApiService } from '../../core/api.service';

@Component({selector:'app-workspace',standalone:true,imports:[FormsModule,DatePipe,RouterLink],templateUrl:'./workspace.component.html'})
export class WorkspaceComponent {
  api=inject(ApiService); data=signal<any>(null); error=signal(''); status=signal(''); busy=signal(false);
  assignment={text:'',assignee:'',project:''};
  log={project:'',date:new Date().toLocaleDateString('en-CA'),minutes:60,summary:''};
  constructor(){this.load();}
  load(){this.api.get<any>('/workspace/').subscribe({next:d=>this.data.set(d),error:e=>this.fail(e)});}
  fail(e:any){this.busy.set(false);this.error.set(e.error?.detail || JSON.stringify(e.error || 'Could not connect. Please try again.'));}
  submit(kind:'task'|'log'|'membership'){
    if(this.busy())return;this.busy.set(true);this.error.set('');this.status.set('');
    this.api.post('/workspace/'+(kind==='log'?'logs/':kind==='membership'?'memberships/':''),kind==='log'?this.log:this.assignment).subscribe({next:()=>{this.busy.set(false);this.status.set(kind==='log'?'Daily work saved.':kind==='membership'?'Project member added.':'Work assigned.');if(kind==='log')this.log.summary='';if(kind==='task')this.assignment.text='';this.load();},error:e=>this.fail(e)});
  }
  complete(t:any){this.api.patch('/workspace/tasks/'+t.id+'/',{done:!t.done}).subscribe({next:()=>this.load(),error:e=>this.fail(e)});}
}
