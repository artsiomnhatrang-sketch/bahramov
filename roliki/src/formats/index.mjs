// Все форматы роликов. Новый формат: тексты в texts/ + строчка здесь.
import { buildBlokirovka } from './blokirovka.mjs';
import { makeFormat } from './common.mjs';
import { OHVATY } from '../texts/ohvaty.mjs';
import { AVTOMATIZACIYA } from '../texts/avtomatizaciya.mjs';
import { buildScenarii } from './scenarii.mjs';
import { UZHE } from '../texts/uzhe.mjs';
import { POISK } from '../texts/poisk.mjs';
import { POISK3 } from '../texts/poisk-v3.mjs';

export const FORMATS = {
  blokirovka: buildBlokirovka,
  ohvaty: makeFormat(OHVATY, { label: 'Охваты Instagram' }),
  avtomatizaciya: makeFormat(AVTOMATIZACIYA, { label: 'Автоматизация Instagram' }),
  scenarii: buildScenarii,
  uzhe: makeFormat(UZHE, { label: 'Ограничения Instagram' }),
  poisk: makeFormat(POISK, { label: 'Безопасность аккаунтов' }),
  poisk3: makeFormat(POISK3, { label: 'Безопасность аккаунтов' }), // монтаж v3 (09.10), собирать с --v3
};
