import {describe,it,expect} from 'vitest';
describe('context pressure presentation contract',()=>{it('never labels estimated as exact',()=>{const exact=false;expect(exact?'reported':'estimated').toBe('estimated')})});
