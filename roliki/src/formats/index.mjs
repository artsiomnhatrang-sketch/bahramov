// Все форматы роликов. Новый формат: тексты в texts/ + строчка здесь.
import { buildBlokirovka } from './blokirovka.mjs';
import { makeFormat } from './common.mjs';
import { OHVATY } from '../texts/ohvaty.mjs';
import { AVTOMATIZACIYA } from '../texts/avtomatizaciya.mjs';
import { buildScenarii } from './scenarii.mjs';
import { UZHE } from '../texts/uzhe.mjs';

export const FORMATS = {
  blokirovka: buildBlokirovka,
  ohvaty: makeFormat(OHVATY, { label: 'Охваты Instagram' }),
  avtomatizaciya: makeFormat(AVTOMATIZACIYA, { label: 'Автоматизация Instagram' }),
  scenarii: buildScenarii,
  uzhe: makeFormat(UZHE, { label: 'Ограничения Instagram' }),
};
