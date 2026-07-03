/**
 * V10 选项 B · MSW server 入口
 * G1 闸门: MSW 拦截所有 fetch
 */
import { setupServer } from 'msw/node';
import { handlers } from './handlers';

export const server = setupServer(...handlers);