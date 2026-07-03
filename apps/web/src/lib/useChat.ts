// 模拟数据 + 对话流程 + 意图路由
// 状态管理已拆分为独立 Hooks：useMessages / useProfile / usePlan / useAudit / useConsultation / useSimulation

import { useCallback, useState, useRef } from 'react';
import { useMessages, useAutoScroll } from './useMessages';
import { useProfile, hasCoreInfo, hasAnyInfo, getMissingFields, extractProfileFromText } from './useProfile';
import { usePlan, type SavedPlan } from './usePlan';
import { useAudit } from './useAudit';
import { useConsultation, type ConsultationRecord } from './useConsultation';
import { useSimulation } from './useSimulation';

// ====== 类型导出（保持向后兼容） ======

export type MessageType = 'text' | 'form_card' | 'plan_card' | 'career_card' | 'audit_report' | 'file_upload_prompt' | 'system';

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  type: MessageType;
  content: string;
  data?: any;
  timestamp: Date;
}

export interface UserProfile {
  province?: string;
  score?: number;
  rank?: number;
  subjects?: string[];
  preferences?: {
    region?: string[];
    majorDirection?: string[];
    tuition?: string;
    careerPlan?: string;
  };
}

// Re-export for backward compatibility
export type { SavedPlan } from './usePlan';
export type { ConsultationRecord } from './useConsultation';

// ====== 静态数据 ======

// 欢迎语（阶段1：能力展示，不索取信息）
const WELCOME_MESSAGE: Message = {
  id: 'welcome',
  role: 'assistant',
  type: 'text',
  content: '👋 你好！我是**升学助手**，你的AI志愿规划师 🎓\n\n我可以帮你：\n\n📊 **生成志愿方案** — 告诉我省份+分数，立刻给你「冲稳保」方案\n🔍 **探索职业** — 了解500+种职业的真实情况\n✅ **审核方案** — 上传已有方案，发现隐藏风险\n\n直接试试对我说：「**广东省物理类620分**」～',
  timestamp: new Date(),
};

// 模拟方案数据
const MOCK_PLAN = {
  rush: [
    { university: '华南理工大学', major: '计算机类（广州校区）', estScore: 628, probability: 30, risk: '中', riskType: '正常冲刺', reason: '你的位次8500，近3年该专业最低位次7500-8200，差距在可冲刺范围。华南理工计算机学科评估A-，珠三角就业认可度高。' },
    { university: '中山大学', major: '电子信息类', estScore: 632, probability: 25, risk: '较高', riskType: '位次差距较大', reason: '中大电信近3年位次波动6800-8000，你的位次略低于最低值。但2026年该专业扩招8%，值得冲刺。' },
    { university: '暨南大学', major: '网络空间安全', estScore: 625, probability: 35, risk: '中', riskType: '专业较新', reason: '暨大网安2024年首次招生，近2年位次7500-9000。专业前景好但历史数据少，参考需谨慎。' },
    { university: '深圳大学', major: '计算机科学与技术（腾班）', estScore: 624, probability: 38, risk: '中', riskType: '竞争激烈', reason: '深大腾班近年热度飙升，录取位次持续走高。但深大计算机整体实力强，深圳就业优势明显。' },
    { university: '广东工业大学', major: '人工智能', estScore: 618, probability: 40, risk: '低', riskType: '正常冲刺', reason: '广工AI专业2025年首次招生，首年位次9000。第二年通常位次上升，但你的位次仍有一定把握。' },
  ],
  stable: [
    { university: '华南师范大学', major: '计算机科学与技术', estScore: 615, probability: 60, risk: '低', riskType: '—', reason: '华师计算机近3年最低位次8500-9500，你的位次在稳妥区间。师范院校计算机专业性价比高，保研率约15%。' },
    { university: '暨南大学', major: '软件工程', estScore: 612, probability: 65, risk: '低', riskType: '—', reason: '暨大软工近3年最低位次8200-9500，匹配度高。珠海校区环境好，实习机会多。' },
    { university: '深圳大学', major: '软件工程', estScore: 610, probability: 70, risk: '低', riskType: '—', reason: '深大软工录取位次稳定在9000-10000，你的位次有较大优势。深圳IT产业集中，实习就业便利。' },
    { university: '广东工业大学', major: '计算机科学与技术', estScore: 608, probability: 75, risk: '低', riskType: '—', reason: '广工计算机是传统优势专业，近3年位次9500-11000。工科实力扎实，广州就业市场认可度高。' },
    { university: '华南农业大学', major: '数据科学与大数据技术', estScore: 605, probability: 78, risk: '低', riskType: '—', reason: '华农数据科学近年发展快，位次10000-12000。双一流高校，性价比突出。' },
    { university: '广州大学', major: '网络工程', estScore: 600, probability: 80, risk: '低', riskType: '—', reason: '广大网工录取位次稳定在11000-13000，保底稳妥。广州本地就业网络广。' },
    { university: '广东外语外贸大学', major: '软件工程', estScore: 598, probability: 80, risk: '低', riskType: '—', reason: '广外软工偏金融科技方向，位次11000-13500。适合对金融+技术交叉领域感兴趣的同学。' },
    { university: '东莞理工学院', major: '计算机科学与技术', estScore: 590, probability: 82, risk: '低', riskType: '—', reason: '莞工计算机近年发展迅速，位次13000-15000。东莞制造业智能化转型带来大量就业机会。' },
  ],
  safe: [
    { university: '佛山科学技术学院', major: '计算机科学与技术', estScore: 575, probability: 90, risk: '低', riskType: '—', reason: '佛科院计算机录取位次15000-18000。佛山制造业强市，IT人才需求大。' },
    { university: '五邑大学', major: '软件工程', estScore: 565, probability: 92, risk: '低', riskType: '—', reason: '五邑大学软工位次17000-20000，保底安全。江门生活成本低，适合稳定发展。' },
    { university: '惠州学院', major: '计算机科学与技术', estScore: 558, probability: 95, risk: '低', riskType: '—', reason: '惠州学院计算机位次19000-23000，保底充分。惠州电子信息产业发达。' },
    { university: '肇庆学院', major: '数据科学与大数据技术', estScore: 550, probability: 96, risk: '低', riskType: '—', reason: '肇庆学院数据科学位次21000-25000，录取把握极高。肇庆新区大数据产业园提供就业机会。' },
    { university: '韶关学院', major: '计算机科学与技术', estScore: 545, probability: 98, risk: '低', riskType: '—', reason: '韶关学院计算机位次24000-28000，录取把握极高。作为保底选择非常安全。' },
  ],
};

// 模拟审核报告
const MOCK_AUDIT_REPORT = {
  overallScore: 4.0,
  summary: '方案整体质量良好，冲稳保梯度基本合理。发现1个关键风险和2个需关注项。',
  riskItems: [
    { level: 'high', text: '第3志愿华南理工-软件工程：近3年最低位次12000，你的位次15000，录取概率<20%，建议下调或替换为位次更匹配的院校。' },
    { level: 'medium', text: '冲刺档占比40%（6/15），建议控制在25-30%，可将2所冲刺院校下调至稳妥档。' },
    { level: 'medium', text: '第8志愿专业组内含3个非计算机专业，存在调剂风险，建议优先选择纯净度高的专业组。' },
  ],
  distribution: { rush: 6, stable: 5, safe: 4 },
  goodPoints: [
    '保底档位次覆盖充分，无滑档风险',
    '专业方向一致性好（以计算机/电子为主）',
    '院校地域集中在珠三角，符合偏好',
  ],
};

// 职业解读数据
const MOCK_CAREER_DATA: Record<string, any> = {
  '人工智能工程师': {
    content: '🤖 **人工智能工程师**\n\n**【工作内容】** 设计、开发和部署AI算法模型，包括机器学习、深度学习、自然语言处理等方向，解决实际业务问题。\n\n**【薪资范围】**\n• 应届：15-25万/年\n• 3年经验：25-45万/年\n• 5年+：40-80万/年\n• 资深/专家：80万+/年\n（2026年广东地区数据）\n\n**【学历要求】** 本科及以上，硕士占比60%+，头部企业偏好985/211硕士\n\n**【核心技能】** Python、机器学习框架（PyTorch/TensorFlow）、数学基础（线代/概率论/优化）、工程能力\n\n**【发展路径】** 算法工程师 → 高级算法工程师 → AI架构师/技术专家 → 技术总监/首席科学家\n\n**【行业前景】** 🔥 高增长赛道，未来5年人才缺口持续扩大。广东AI产业规模超2000亿，深圳/广州为核心城市。',
    relatedMajors: [
      { name: '计算机科学与技术', match: 5 },
      { name: '人工智能', match: 5 },
      { name: '软件工程', match: 4 },
      { name: '数据科学与大数据技术', match: 4 },
      { name: '电子信息工程', match: 3 },
    ],
  },
  '临床医生': {
    content: '🏥 **临床医生**\n\n**【工作内容】** 诊断疾病、制定治疗方案、进行手术操作、管理住院患者、参与科研和教学工作。\n\n**【薪资范围】**\n• 规培期间：8-12万/年\n• 住院医师：12-20万/年\n• 主治医师：20-40万/年\n• 副主任/主任医师：40-80万+/年\n（2026年广东三甲医院参考）\n\n**【学历要求】** 临床医学本科5年 + 规培3年 = 至少8年。三甲医院基本要求博士。\n\n**【核心技能】** 临床诊断能力、手术技能、沟通能力、抗压能力、终身学习\n\n**【发展路径】** 医学生 → 规培医师 → 住院医师 → 主治医师 → 副主任医师 → 主任医师\n\n**【行业前景】** 需求稳定增长，人口老龄化推动医疗需求。广东医疗资源集中，三甲医院竞争激烈。⚠️ 投入周期长、压力大，需充分评估。',
    relatedMajors: [
      { name: '临床医学', match: 5 },
      { name: '口腔医学', match: 4 },
      { name: '基础医学', match: 3 },
      { name: '医学影像学', match: 3 },
      { name: '预防医学', match: 2 },
    ],
  },
};

// ====== 主 Hook ======

export function useChat() {
  // === 子 Hooks ===
  const {
    messages,
    setMessages,
    addMessage,
    updateLastMessageOfType,
    messagesEndRef,
    scrollToBottom,
  } = useMessages([WELCOME_MESSAGE]);

  const {
    userProfile,
    setUserProfile,
    updateProfile,
    isComplete: profileComplete,
    hasPartial: profilePartial,
    missing: profileMissing,
  } = useProfile();

  const {
    currentPlan,
    setCurrentPlan,
    savedPlans,
    savePlan,
    deletePlan,
    updatePlanName,
  } = usePlan();

  const { currentAuditReport, setCurrentAuditReport } = useAudit();

  const {
    activeRecordId,
    newConsultation,
    loadConsultation,
  } = useConsultation(messages, userProfile, currentPlan, currentAuditReport);

  const { isTyping, simulateTyping } = useSimulation();

  // 自动滚动
  useAutoScroll(messages, isTyping, scrollToBottom);

  // === 咨询管理 ===
  const newChat = useCallback(() => {
    newConsultation();
    setMessages([{ ...WELCOME_MESSAGE, timestamp: new Date() }]);
    setUserProfile({});
    setCurrentPlan(null);
    setCurrentAuditReport(null);
  }, [newConsultation, setMessages, setUserProfile, setCurrentPlan, setCurrentAuditReport]);

  const resumeChat = useCallback(
    (id: string): boolean => {
      const record = loadConsultation(id);
      if (!record) return false;
      setMessages(
        record.messages.length
          ? record.messages
          : [{ ...WELCOME_MESSAGE, timestamp: new Date() }]
      );
      setUserProfile(record.userProfile || {});
      setCurrentPlan(record.currentPlan || null);
      setCurrentAuditReport(record.currentAuditReport || null);
      return true;
    },
    [loadConsultation, setMessages, setUserProfile, setCurrentPlan, setCurrentAuditReport]
  );

  // === 意图路由 — 核心 sendMessage ===
  const [pendingAction, setPendingActionState] = useState<string | null>(null);

  // 用 ref 追踪 pendingAction 避免闭包陈旧问题
  const pendingActionRef = useRef<string | null>(null);
  const setPendingAction = (val: string | null) => {
    pendingActionRef.current = val;
    setPendingActionState(val);
  };

  const sendMessage = useCallback(async (text: string) => {
    const lowerText = text.toLowerCase();

    // 添加用户消息
    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      type: 'text',
      content: text,
      timestamp: new Date(),
    };
    addMessage(userMsg);

    // 解析用户输入，更新画像
    const prevProfile = { ...userProfile };
    const nextProfile = extractProfileFromText(text, userProfile);
    setUserProfile(nextProfile);

    // 判断信息状态变化
    const wasComplete = hasCoreInfo(prevProfile);
    const isNowComplete = hasCoreInfo(nextProfile);

    await simulateTyping(800);

    // ========================================
    // 意图路由（优先级从高到低）
    // ========================================

    // 1. 审核意图
    if (lowerText.includes('审核') || lowerText.includes('检查方案') || lowerText.includes('帮我看')) {
      if (pendingActionRef.current !== 'audit') {
        addMessage({
          id: `audit-prompt-${Date.now()}`,
          role: 'assistant',
          type: 'file_upload_prompt',
          content: '好的！请把你的方案发给我审核，支持以下方式：\n• 📝 直接粘贴文本\n• 📎 上传Excel/图片/PDF',
          data: { modes: ['text', 'excel', 'image', 'pdf'] },
          timestamp: new Date(),
        });
        setPendingAction('audit');
      }
      return;
    }

    // 2. 审核等待中 + 用户粘贴方案内容
    if (pendingActionRef.current === 'audit' && (text.includes('大学') || text.includes('学院'))) {
      await simulateTyping(1500);
      addMessage({
        id: `audit-parse-${Date.now()}`,
        role: 'assistant',
        type: 'text',
        content: '我识别到你的方案包含15个志愿，以计算机/电子类专业为主。正在审核中...',
        timestamp: new Date(),
      });
      await simulateTyping(2000);
      setCurrentAuditReport(MOCK_AUDIT_REPORT);
      addMessage({
        id: `audit-report-${Date.now()}`,
        role: 'assistant',
        type: 'audit_report',
        content: '📊 方案审核报告',
        data: MOCK_AUDIT_REPORT,
        timestamp: new Date(),
      });
      setPendingAction(null);
      return;
    }
    setPendingAction(null);

    // 3. 职业解读
    if (lowerText.includes('职业') || lowerText.includes('工程师') || lowerText.includes('医生') || (lowerText.includes('做什么') && !lowerText.includes('方案'))) {
      let careerKey = '人工智能工程师';
      if (lowerText.includes('医生') || lowerText.includes('临床')) careerKey = '临床医生';
      const careerData = MOCK_CAREER_DATA[careerKey];
      if (careerData) {
        addMessage({
          id: `career-${Date.now()}`,
          role: 'assistant',
          type: 'career_card',
          content: careerData.content,
          data: { relatedMajors: careerData.relatedMajors, careerName: careerKey },
          timestamp: new Date(),
        });
      }
      return;
    }

    // 4. 政策咨询
    if (lowerText.includes('政策') || lowerText.includes('平行志愿') || lowerText.includes('退档') || lowerText.includes('调剂')) {
      addMessage({
        id: `policy-${Date.now()}`,
        role: 'assistant',
        type: 'text',
        content: '📖 **关于平行志愿**\n\n平行志愿是高考录取的主要方式。简单说就是：\n\n1. **分数优先**：所有考生按分数从高到低排队\n2. **遵循志愿**：轮到你的分数时，按你填报的志愿顺序依次检索\n3. **一轮投档**：一旦投档到某所院校，后面的志愿就不再检索\n\n💡 **举例**：你的分数620分排第8500名。系统先处理第8499名考生的所有志愿，再轮到你。然后按你的第1志愿→第2志愿→...依次检索，哪个学校没满就投档到哪个。\n\n⚠️ 根据2026年广东省高考政策，请以省教育考试院官方发布为准。',
        timestamp: new Date(),
      });
      return;
    }

    // 5. 方案调整
    if (currentPlan && (lowerText.includes('调整') || lowerText.includes('换') || lowerText.includes('去掉') || lowerText.includes('珠三角') || lowerText.includes('长三角') || lowerText.includes('北京'))) {
      const isRegionFilter = lowerText.includes('珠三角') || lowerText.includes('长三角') || lowerText.includes('北京');
      const isRemove = lowerText.includes('去掉') || lowerText.includes('移除');
      const regionTarget = lowerText.includes('珠三角') ? '珠三角' : lowerText.includes('长三角') ? '长三角' : lowerText.includes('北京') ? '北京' : '';

      const adjustedPlan = JSON.parse(JSON.stringify(MOCK_PLAN));
      const adjustMark = (item: any) => ({ ...item, adjusted: true });

      if (isRegionFilter && regionTarget) {
        const regionKeyword = regionTarget === '珠三角'
          ? ['深圳', '广州', '东莞', '佛山', '广东', '暨南', '华南', '中山', '江门', '惠州', '肇庆', '韶关']
          : ['北京'];
        const sortByRegion = (items: any[]) => {
          const matched = items.filter((i: any) => regionKeyword.some((k: string) => i.university.includes(k)));
          const unmatched = items.filter((i: any) => !regionKeyword.some((k: string) => i.university.includes(k)));
          return [...matched.map(adjustMark), ...unmatched];
        };
        adjustedPlan.rush = sortByRegion(adjustedPlan.rush);
        adjustedPlan.stable = sortByRegion(adjustedPlan.stable);
        adjustedPlan.safe = sortByRegion(adjustedPlan.safe);
      }

      if (isRemove) {
        adjustedPlan.rush = adjustedPlan.rush.slice(0, 4);
        adjustedPlan.stable = adjustedPlan.stable.slice(0, 6);
      }

      const tweakProbability = (items: any[]) => items.map((item: any) => ({
        ...item,
        probability: Math.min(98, Math.max(15, item.probability + Math.floor(Math.random() * 8) - 3)),
      }));
      adjustedPlan.rush = tweakProbability(adjustedPlan.rush);
      adjustedPlan.stable = tweakProbability(adjustedPlan.stable);

      await simulateTyping(1200);

      const changes: string[] = [];
      if (isRegionFilter && regionTarget) changes.push(`🌍 聚焦**${regionTarget}**地区院校`);
      if (isRemove) changes.push('🗑️ 移除了非相关专业院校');
      changes.push('📊 重新计算了录取概率');

      // 就地更新方案卡片（不新增消息，直接更新已有的 plan_card）
      updateLastMessageOfType('plan_card', {
        plan: adjustedPlan,
        profile: nextProfile,
        adjusted: true,
      });
      setCurrentPlan(adjustedPlan);

      // 仅追加一条简洁的文本确认
      addMessage({
        id: `adjust-${Date.now()}`,
        role: 'assistant',
        type: 'text',
        content: `已更新！${changes.map(c => `• ${c}`).join('  ')}\n\n还需要继续调整吗？`,
        timestamp: new Date(),
      });
      return;
    }

    // 6. 核心信息刚补全 → 自动生成方案
    if (isNowComplete && !wasComplete) {
      await simulateTyping(2000);
      addMessage({
        id: `auto-gen-${Date.now()}`,
        role: 'assistant',
        type: 'text',
        content: `收到！${nextProfile.province}${nextProfile.subjects?.[0]}类${nextProfile.score}分，位次${nextProfile.rank || '待确认'}，这个成绩在广东属于不错的水平。\n\n我来帮你生成一份志愿方案——`,
        timestamp: new Date(),
      });
      await simulateTyping(2500);
      const planMsg: Message = {
        id: `plan-${Date.now()}`,
        role: 'assistant',
        type: 'plan_card',
        content: '📊 你的志愿方案已生成',
        data: { plan: MOCK_PLAN, profile: nextProfile },
        timestamp: new Date(),
      };
      setCurrentPlan(MOCK_PLAN);
      addMessage(planMsg);
      await simulateTyping(500);
      addMessage({
        id: `follow-${Date.now()}`,
        role: 'assistant',
        type: 'text',
        content: '需要调整吗？比如：\n• "想去**珠三角以外**的地区"\n• "只看**有保研资格**的学校"\n• "了解一下**人工智能工程师**这个职业"\n• "帮我**审核这份方案**"',
        timestamp: new Date(),
      });
      return;
    }

    // 7. 已有完整信息 + 明确要求生成/推荐
    if (isNowComplete && (lowerText.includes('生成方案') || lowerText.includes('推荐') || lowerText.includes('志愿方案') || lowerText.includes('填报') || lowerText.includes('方案'))) {
      await simulateTyping(2500);
      const planMsg: Message = {
        id: `plan-${Date.now()}`,
        role: 'assistant',
        type: 'plan_card',
        content: '📊 你的志愿方案已生成',
        data: { plan: MOCK_PLAN, profile: nextProfile },
        timestamp: new Date(),
      };
      setCurrentPlan(MOCK_PLAN);
      addMessage(planMsg);
      await simulateTyping(500);
      addMessage({
        id: `follow-${Date.now()}`,
        role: 'assistant',
        type: 'text',
        content: '需要调整吗？比如调整地区偏好、专业方向，或者了解某个职业？',
        timestamp: new Date(),
      });
      return;
    }

    // 8. 信息不足 → 弹出表单
    if (!isNowComplete && (text.includes('物理') || text.includes('历史') || text.match(/(\d{3})\s*分/) || text.match(/(广东|河南|山东|四川|江苏|浙江|湖北|湖南|北京|上海|天津|重庆|福建|安徽|河北|辽宁|吉林|黑龙江|陕西|山西|江西|广西|云南|贵州|海南|甘肃|宁夏|青海|西藏|新疆|内蒙古)/) || lowerText.includes('推荐') || lowerText.includes('生成方案') || lowerText.includes('填报'))) {
      const missing = getMissingFields(nextProfile);
      addMessage({
        id: `form-${Date.now()}`,
        role: 'assistant',
        type: 'form_card',
        content: '还差一点信息，我来帮你完善～',
        data: { missingFields: missing, currentProfile: nextProfile },
        timestamp: new Date(),
      });
      return;
    }

    // 9. 默认：温暖引导
    if (hasAnyInfo(nextProfile)) {
      const missing = getMissingFields(nextProfile);
      addMessage({
        id: `reply-${Date.now()}`,
        role: 'assistant',
        type: 'text',
        content: `好的，我记住了${missing.length === 1 ? '一部分信息' : '一些信息'}！\n\n还差 ${missing.map(m => `**${m}**`).join('、')} 就能帮你生成志愿方案了～ 告诉我吧，不急😊`,
        timestamp: new Date(),
      });
    } else {
      addMessage({
        id: `reply-${Date.now()}`,
        role: 'assistant',
        type: 'text',
        content: '你想了解什么呢？😊\n\n不管是**职业探索**、**政策解读**，还是**志愿填报**的问题，都可以跟我说～\n\n比如直接告诉我你在哪个省、考了多少分，我就能帮你规划志愿了！',
        timestamp: new Date(),
      });
    }
  }, [addMessage, simulateTyping, userProfile, currentPlan, setUserProfile, setCurrentPlan, setCurrentAuditReport, updateLastMessageOfType]);

  // 表单提交
  const submitForm = useCallback(async (formData: Record<string, any>) => {
    updateProfile(formData);
    const merged = { ...userProfile, ...formData };
    await simulateTyping(1500);

    const planMsg: Message = {
      id: `plan-${Date.now()}`,
      role: 'assistant',
      type: 'plan_card',
      content: '📊 你的志愿方案已生成',
      data: { plan: MOCK_PLAN, profile: merged },
      timestamp: new Date(),
    };
    setCurrentPlan(MOCK_PLAN);
    addMessage(planMsg);

    await simulateTyping(500);
    addMessage({
      id: `follow-${Date.now()}`,
      role: 'assistant',
      type: 'text',
      content: '需要调整吗？比如调整地区偏好、专业方向，或者了解某个职业？',
      timestamp: new Date(),
    });
  }, [addMessage, simulateTyping, userProfile, updateProfile, setCurrentPlan]);

  // 文件上传
  const handleFileUpload = useCallback(async (type: 'text' | 'excel' | 'image' | 'pdf', file?: File, textContent?: string) => {
    const uploadLabels: Record<string, string> = { text: '粘贴文本', excel: 'Excel文件', image: '图片', pdf: 'PDF文件' };

    addMessage({
      id: `user-upload-${Date.now()}`,
      role: 'user',
      type: 'text',
      content: file ? `上传了${uploadLabels[type]}：${file.name}` : `通过${uploadLabels[type]}提交了志愿方案`,
      timestamp: new Date(),
    });

    await simulateTyping(1200);
    addMessage({
      id: `upload-parse-${Date.now()}`,
      role: 'assistant',
      type: 'text',
      content: file
        ? `已收到你的${uploadLabels[type]}（${(file.size / 1024).toFixed(1)}KB），正在解析志愿方案...`
        : '已收到你粘贴的志愿方案，正在解析...',
      timestamp: new Date(),
    });

    await simulateTyping(2000);
    addMessage({
      id: `upload-parsed-${Date.now()}`,
      role: 'assistant',
      type: 'text',
      content: '✅ 识别到你的方案包含15个志愿，以计算机/电子类专业为主。正在逐项审核中...',
      timestamp: new Date(),
    });

    await simulateTyping(2500);
    setCurrentAuditReport(MOCK_AUDIT_REPORT);
    addMessage({
      id: `audit-report-${Date.now()}`,
      role: 'assistant',
      type: 'audit_report',
      content: '📊 方案审核报告',
      data: MOCK_AUDIT_REPORT,
      timestamp: new Date(),
    });
    setPendingAction(null);
  }, [addMessage, simulateTyping, setCurrentAuditReport]);

  return {
    activeRecordId,
    messages,
    isTyping,
    sendMessage,
    submitForm,
    handleFileUpload,
    userProfile,
    currentPlan,
    currentAuditReport,
    messagesEndRef,
    savedPlans,
    savePlan,
    deletePlan,
    updatePlanName,
    newConsultation: newChat,
    loadConsultation: resumeChat,
  };
}
