import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { ApplicationConfig, provideZoneChangeDetection } from '@angular/core';
import { provideAnimations } from '@angular/platform-browser/animations';
import { provideRouter, withComponentInputBinding, withInMemoryScrolling, withHashLocation } from '@angular/router';
import { deployment } from './core/deployment';

import { routes } from './app.routes';
import { tokenInterceptor } from './core/token.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(
      routes,
      ...(deployment.pages ? [withHashLocation()] : []),
      withComponentInputBinding(),
      withInMemoryScrolling({ scrollPositionRestoration: 'top' }),
    ),
    provideHttpClient(withInterceptors([tokenInterceptor])),
    provideAnimations(),
  ],
};
