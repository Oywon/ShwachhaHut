import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { BrowserRouter, Link, Navigate, Route, Routes, useNavigate } from 'react-router-dom'
import {
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  Bell,
  Check,
  ChevronDown,
  CircleHelp,
  ClipboardCheck,
  Leaf,
  LogOut,
  MapPin,
  Menu,
  PackageCheck,
  ShieldCheck,
  Sprout,
  TrendingUp,
  Wheat,
  X,
} from 'lucide-react'
import './App.css'

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1'
const TODAY = new Date().toISOString().slice(0, 10)

type User = { id: string; name: string; phone: string; role: string }
type Transaction = {
  id: string
  farmer_id: string
  buyer_id: string
  crop: string
  quantity_kg: string
  price_per_kg: string
  district: string
  upazila: string
  sale_date: string
  status: string
  created_at: string
}
type Buyer = { id: string; name: string; role: string }
type Lot = {
  id: string
  transaction_id: string
  crop: string
  original_quantity_kg: string
  remaining_quantity_kg: string
  purpose: string | null
  storage_location: string | null
  expected_release_date: string | null
}
type PriceData = {
  minimum: string
  maximum: string
  crop: string
  district: string
  upazila: string
  production_cost_per_kg: string
  methodology: string
  market_observations: { market: string; price_per_kg: string; source: string; simulated: boolean }[]
  source_label: string
  simulated: boolean
}

async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = sessionStorage.getItem('access_token')
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init.headers,
    },
  })
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new Error(body?.detail || `Request failed (${response.status})`)
  }
  return response.json() as Promise<T>
}

function App() {
  const queryClient = useQueryClient()
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/market" element={<MarketPage />} />
        <Route path="/login" element={<AuthPage mode="login" />} />
        <Route path="/register" element={<AuthPage mode="register" />} />
        <Route
          path="/app"
          element={<DashboardPage onSignOut={() => {
            sessionStorage.removeItem('access_token')
            queryClient.clear()
          }} />}
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

function Brand({ inverse = false }: { inverse?: boolean }) {
  return (
    <Link className={`brand${inverse ? ' brand-inverse' : ''}`} to="/" aria-label="SwachchhoHat home">
      <span className="brand-mark"><Sprout size={21} strokeWidth={2.2} /></span>
      <span>স্বচ্ছহাট<span className="brand-latin">SwachchhoHat</span></span>
    </Link>
  )
}

function SiteHeader() {
  const [menuOpen, setMenuOpen] = useState(false)
  return (
    <header className="site-header">
      <div className="container header-inner">
        <Brand />
        <button className="mobile-menu" onClick={() => setMenuOpen(!menuOpen)} aria-label="Toggle navigation">
          {menuOpen ? <X size={21} /> : <Menu size={21} />}
        </button>
        <nav className={`main-nav${menuOpen ? ' nav-open' : ''}`}>
          <Link to="/market">বাজারদর <span>Market prices</span></Link>
          <a href="/#how-it-works">যেভাবে কাজ করে</a>
          <a href="/#radar">AI Radar</a>
          <Link className="nav-login" to="/login">লগইন</Link>
          <Link className="button button-primary button-small" to="/register">শুরু করুন <ArrowRight size={15} /></Link>
        </nav>
      </div>
    </header>
  )
}

function HomePage() {
  return (
    <div className="home-page">
      <SiteHeader />
      <main>
        <section className="hero-section">
          <div className="container hero-layout">
            <div className="hero-copy">
              <div className="eyebrow"><span className="eyebrow-dot" /> কৃষি বাজারে স্বচ্ছতার নতুন উদ্যোগ</div>
              <h1>কৃষকের ন্যায্য দাম,<br /><span>বাজারের স্বচ্ছতা।</span></h1>
              <p className="hero-description">
                নির্ভরযোগ্য বাজারতথ্য, দুই পক্ষের সম্মতিতে বিক্রির রেকর্ড, আর ব্যাখ্যাযোগ্য নজরদারি—সব এক জায়গায়।
              </p>
              <div className="hero-actions">
                <Link className="button button-primary" to="/market">আজকের বাজারদর দেখুন <ArrowRight size={17} /></Link>
                <Link className="button button-quiet" to="/register">প্ল্যাটফর্মে যোগ দিন</Link>
              </div>
              <div className="hero-note"><ShieldCheck size={16} /> তথ্য যাচাইযোগ্য, ব্যক্তিগত তথ্য সুরক্ষিত</div>
            </div>
            <div className="hero-visual" aria-label="Illustration of an agricultural market">
              <div className="visual-orbit orbit-one" />
              <div className="visual-orbit orbit-two" />
              <div className="sun-disc" />
              <div className="field field-back" />
              <div className="field field-front" />
              <div className="visual-stem stem-one" /><div className="visual-stem stem-two" /><div className="visual-stem stem-three" />
              <div className="floating-price">
                <span className="floating-icon"><TrendingUp size={17} /></span>
                <span><small>ন্যায্য দাম</small><strong>তথ্যভিত্তিক</strong></span>
                <span className="price-trend"><ArrowUpRight size={16} /></span>
              </div>
              <div className="visual-caption"><MapPin size={14} /> ফরিদপুর · পাইলট বাজার</div>
            </div>
          </div>
          <div className="hero-bottom container">
            <span>কৃষকের জন্য তৈরি, স্বচ্ছতার জন্য নির্মিত</span>
            <div><span className="bottom-seed"><Leaf size={15} /></span> <b>Faridpur pilot</b><i /> Onion market</div>
          </div>
        </section>

        <section className="trust-strip">
          <div className="container trust-inner">
            <span>একটি ন্যায্য বাজারে দরকার</span>
            <div><ShieldCheck size={17} /> যাচাইযোগ্য লেনদেন</div>
            <div><TrendingUp size={17} /> ব্যাখ্যাযোগ্য দাম</div>
            <div><PackageCheck size={17} /> দৃশ্যমান মজুত</div>
          </div>
        </section>

        <section className="section section-how" id="how-it-works">
          <div className="container">
            <div className="section-heading">
              <span className="eyebrow plain">স্বচ্ছতার তিন ধাপ</span>
              <h2>একটি বিক্রি থেকে<br /><span>বিশ্বাসযোগ্য বাজারতথ্য।</span></h2>
              <p>প্রতিটি ধাপ দায়িত্বশীল মানুষের নিয়ন্ত্রণে; প্রযুক্তি তথ্য সাজায়, সিদ্ধান্ত চাপিয়ে দেয় না।</p>
            </div>
            <div className="steps-grid">
              <article className="step-card">
                <span className="step-number">01</span><span className="step-icon"><Wheat size={21} /></span>
                <h3>ন্যায্য দাম জানুন</h3><p>উৎপাদন ব্যয় ও স্থানীয় বাজার পর্যবেক্ষণের ভিত্তিতে হিসাবের ব্যাখ্যা দেখুন।</p>
              </article>
              <article className="step-card">
                <span className="step-number">02</span><span className="step-icon"><ClipboardCheck size={21} /></span>
                <h3>দুই পক্ষের সম্মতি</h3><p>কৃষক বিক্রির তথ্য জমা দেন, ক্রেতা নিশ্চিত করলে তবেই যাচাইকৃত লট তৈরি হয়।</p>
              </article>
              <article className="step-card" id="radar">
                <span className="step-number">03</span><span className="step-icon"><ShieldCheck size={21} /></span>
                <h3>মানুষের তত্ত্বাবধানে নজরদারি</h3><p>অস্বাভাবিক সংকেত পর্যালোচনার জন্য যায়—এটি অভিযোগ বা আইনি সিদ্ধান্ত নয়।</p>
              </article>
            </div>
          </div>
        </section>

        <section className="cta-section">
          <div className="container cta-panel">
            <div><span className="eyebrow plain">স্বচ্ছ বাজার, শক্তিশালী কৃষক</span><h2>আপনার এলাকার দাম<br />দেখে শুরু করুন।</h2></div>
            <Link to="/market" className="button button-light">বাজারদর দেখুন <ArrowRight size={16} /></Link>
            <span className="cta-leaf"><Leaf size={74} /></span>
          </div>
        </section>
      </main>
      <SiteFooter />
    </div>
  )
}

function MarketPage() {
  const [upazila, setUpazila] = useState('Faridpur Sadar')
  const price = useQuery({
    queryKey: ['fair-range', upazila],
    queryFn: () => api<PriceData>(`/prices/fair-range?district=Faridpur&upazila=${encodeURIComponent(upazila)}&crop=onion`),
  })
  return (
    <div className="app-shell">
      <SiteHeader />
      <main className="container market-main">
        <div className="page-kicker"><span className="eyebrow plain">বাজার তথ্য</span><span className="fresh-dot" /> API থেকে সর্বশেষ হিসাব</div>
        <div className="market-heading"><div><h1>আজকের পেঁয়াজের দাম</h1><p>দাম নির্দেশনামূলক; এটি বাধ্যতামূলক বা সরকারি নির্ধারিত মূল্য নয়।</p></div>
          <label className="location-select"><MapPin size={16} /><select value={upazila} onChange={(event) => setUpazila(event.target.value)}><option>Faridpur Sadar</option><option>Boalmari</option><option>Nagarkanda</option></select><ChevronDown size={15} /></label>
        </div>
        {price.isPending && <div className="state-card">বাজারের হিসাব লোড হচ্ছে…</div>}
        {price.isError && <div className="state-card error-state"><CircleHelp size={22} /><div><strong>এই এলাকার দামের তথ্য পাওয়া যায়নি</strong><p>{price.error.message}. Backend চালু আছে এবং demo seed করা হয়েছে কি না দেখুন।</p></div></div>}
        {price.data && <>
          {price.data.simulated && <div className="simulation-banner"><span>DEMO DATA</span> এই পাইলট পরিবেশে প্রদর্শিত তথ্য সিমুলেটেড; বাস্তব বাজারদর নয়।</div>}
          <section className="price-feature">
            <div className="price-feature-top"><span className="metric-label">ন্যায্য দামের হিসাব · প্রতি কেজি</span><span className="metric-date"><MapPin size={13} /> {price.data.upazila}, {price.data.district}</span></div>
            <div className="price-range"><span>৳{Number(price.data.minimum).toFixed(2)}</span><i>—</i><span>৳{Number(price.data.maximum).toFixed(2)}</span></div>
            <p className="price-method">{price.data.methodology}</p>
            <div className="price-feature-foot"><span><ShieldCheck size={15} /> ব্যাখ্যাযোগ্য হিসাব</span><span>উৎস: {price.data.source_label}</span></div>
          </section>
          <div className="market-grid">
            <section className="content-card">
              <div className="card-title-row"><div><h2>স্থানীয় বাজার পর্যবেক্ষণ</h2><p>সাম্প্রতিক জমাকৃত তথ্য</p></div><TrendingUp size={19} /></div>
              {price.data.market_observations.length ? <div className="observation-list">{price.data.market_observations.map((item, index) => <div className="observation" key={`${item.market}-${index}`}><span className="market-avatar"><MapPin size={16} /></span><span className="observation-name"><strong>{item.market}</strong><small>{item.source}{item.simulated ? ' · সিমুলেটেড' : ''}</small></span><b>৳{Number(item.price_per_kg).toFixed(2)}<small>/ কেজি</small></b></div>)}</div> : <p className="empty-note">এই এলাকার জন্য এখনো কোনো বাজার পর্যবেক্ষণ নেই।</p>}
            </section>
            <section className="content-card methodology-card"><span className="method-icon"><CircleHelp size={20} /></span><h2>হিসাবটি কীভাবে হয়?</h2><p>{price.data.methodology}</p><div className="cost-line"><span>নিবন্ধিত উৎপাদন ব্যয়</span><strong>৳{Number(price.data.production_cost_per_kg).toFixed(2)}/কেজি</strong></div><div className="notice-note">দাম বাজার পর্যবেক্ষণ, তথ্যের মান এবং কনফিগার করা পরামিতির ওপর নির্ভরশীল। পদ্ধতিটি অর্থনৈতিকভাবে যাচাইকৃত পূর্বাভাস নয়।</div></section>
          </div>
        </>}
        <Link className="back-link" to="/"><ArrowDownRight size={15} /> স্বচ্ছহাট সম্পর্কে জানুন</Link>
      </main>
      <SiteFooter />
    </div>
  )
}

function AuthPage({ mode }: { mode: 'login' | 'register' }) {
  const navigate = useNavigate()
  const [error, setError] = useState('')
  const isRegister = mode === 'register'
  const mutation = useMutation({
    mutationFn: (values: Record<string, string>) => api<{ access_token: string; user: User }>(`/auth/${mode === 'login' ? 'login' : 'register'}`, {
      method: 'POST',
      body: JSON.stringify(values),
    }),
    onSuccess: (result) => {
      sessionStorage.setItem('access_token', result.access_token)
      setError('')
      navigate('/app')
    },
    onError: (reason) => setError(reason.message),
  })
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const formData = new FormData(event.currentTarget)
    mutation.mutate(Object.fromEntries(formData.entries()) as Record<string, string>)
  }
  return (
    <div className="auth-page">
      <div className="auth-brand"><Brand /><Link to="/">মূল পাতায় ফিরুন</Link></div>
      <div className="auth-card">
        <span className="auth-icon"><Sprout size={22} /></span>
        <span className="eyebrow plain">{isRegister ? 'নতুন অ্যাকাউন্ট' : 'আপনার অ্যাকাউন্ট'}</span>
        <h1>{isRegister ? 'স্বচ্ছহাটে যোগ দিন' : 'আবার স্বাগতম'}</h1>
        <p>{isRegister ? 'কৃষক বা ক্রেতা হিসেবে নিবন্ধন করুন।' : 'আপনার ফোন নম্বর ও পাসওয়ার্ড দিয়ে প্রবেশ করুন।'}</p>
        <form className="form-stack" onSubmit={submit}>
          {isRegister && <label>নাম<input name="name" required minLength={2} maxLength={120} placeholder="আপনার নাম" /></label>}
          <label>মোবাইল নম্বর<input name="phone" required minLength={7} maxLength={32} placeholder="+8801XXXXXXXXX" autoComplete="tel" /></label>
          <label>পাসওয়ার্ড<input name="password" type="password" required minLength={isRegister ? 10 : 1} maxLength={128} placeholder={isRegister ? 'কমপক্ষে ১০ অক্ষর' : 'আপনার পাসওয়ার্ড'} autoComplete={isRegister ? 'new-password' : 'current-password'} /></label>
          {isRegister && <label>আপনার পরিচয়<select name="role" required defaultValue="farmer"><option value="farmer">কৃষক</option><option value="buyer">ক্রেতা / ব্যবসায়ী</option></select></label>}
          {error && <div className="form-error" role="alert">{error}</div>}
          <button className="button button-primary button-full" disabled={mutation.isPending}>{mutation.isPending ? 'অপেক্ষা করুন…' : isRegister ? 'অ্যাকাউন্ট তৈরি করুন' : 'লগইন করুন'} <ArrowRight size={16} /></button>
        </form>
        <div className="auth-switch">{isRegister ? 'আগে থেকেই অ্যাকাউন্ট আছে?' : 'নতুন এখানে?'} <Link to={isRegister ? '/login' : '/register'}>{isRegister ? 'লগইন করুন' : 'অ্যাকাউন্ট খুলুন'}</Link></div>
        <div className="auth-disclaimer"><ShieldCheck size={15} /> ডেভেলপমেন্ট OTP/ফোন যাচাই এখনো সংযুক্ত নয়।</div>
      </div>
    </div>
  )
}

function DashboardPage({ onSignOut }: { onSignOut: () => void }) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const user = useQuery({ queryKey: ['me'], queryFn: () => api<User>('/users/me'), retry: false })
  const transactions = useQuery({ queryKey: ['transactions'], queryFn: () => api<Transaction[]>('/transactions'), enabled: Boolean(user.data) })
  const buyers = useQuery({ queryKey: ['buyers'], queryFn: () => api<Buyer[]>('/buyers'), enabled: user.data?.role === 'farmer' })
  const lots = useQuery({ queryKey: ['lots'], queryFn: () => api<Lot[]>('/inventory/lots'), enabled: user.data?.role === 'buyer' })
  const [notice, setNotice] = useState('')
  const logout = () => { onSignOut(); navigate('/') }
  if (user.isPending) return <div className="state-card dashboard-loading">Հিসাব যাচাই হচ্ছে…</div>
  if (user.isError) return <Navigate to="/login" replace />
  const reload = async () => { await queryClient.invalidateQueries() }
  async function respond(id: string, confirm: boolean) {
    const reason = confirm ? undefined : window.prompt('বিরোধের কারণ লিখুন:')
    if (!confirm && !reason?.trim()) return
    try {
      await api(`/transactions/${id}/confirm`, { method: 'POST', body: JSON.stringify({ confirm, reason }) })
      setNotice(confirm ? 'লেনদেন নিশ্চিত হয়েছে এবং যাচাইকৃত লট তৈরি হয়েছে।' : 'বিরোধের তথ্য জমা হয়েছে।')
      await reload()
    } catch (error) { setNotice(error instanceof Error ? error.message : 'অনুরোধ ব্যর্থ হয়েছে') }
  }
  return (
    <div className="dashboard-page">
      <header className="dash-header"><div className="container dash-header-inner"><Brand /><div className="dash-user"><span className="user-avatar">{user.data.name.slice(0, 1)}</span><span><strong>{user.data.name}</strong><small>{user.data.role === 'farmer' ? 'কৃষক' : user.data.role === 'buyer' ? 'ক্রেতা' : user.data.role}</small></span><button className="icon-button" onClick={logout} title="লগআউট"><LogOut size={18} /></button></div></div></header>
      <main className="container dashboard-main">
        <div className="welcome-row"><div><span className="eyebrow plain">{user.data.role === 'farmer' ? 'কৃষক পোর্টাল' : 'ক্রেতা পোর্টাল'} · ফরিদপুর</span><h1>স্বাগতম, {user.data.name.split(' ')[0]} <span>👋</span></h1><p>আপনার বাজার কার্যক্রম এক নজরে দেখুন।</p></div><Link to="/market" className="button button-outline">আজকের দাম <ArrowUpRight size={15} /></Link></div>
        {notice && <div className="notice-banner" role="status"><Check size={17} />{notice}<button onClick={() => setNotice('')} aria-label="Dismiss"><X size={16} /></button></div>}
        <section className="dash-metrics">
          <div className="dash-metric"><span className="dash-metric-icon green"><ClipboardCheck size={19} /></span><div><small>মোট লেনদেন</small><strong>{transactions.data?.length ?? '—'}</strong></div><span className="metric-note">আপনার রেকর্ড</span></div>
          <div className="dash-metric"><span className="dash-metric-icon amber"><Bell size={19} /></span><div><small>অপেক্ষমাণ নিশ্চিতকরণ</small><strong>{transactions.data?.filter((item) => item.status === 'pending').length ?? '—'}</strong></div><span className="metric-note">ক্রেতার উত্তর বাকি</span></div>
          <div className="dash-metric"><span className="dash-metric-icon blue"><PackageCheck size={19} /></span><div><small>যাচাইকৃত লট</small><strong>{lots.data?.length ?? (user.data.role === 'farmer' ? '—' : '0')}</strong></div><span className="metric-note">নিশ্চিত বিক্রির পর</span></div>
        </section>
        {user.data.role === 'farmer' ? <FarmerWorkspace buyers={buyers.data ?? []} transactions={transactions.data ?? []} onDone={reload} onError={setNotice} /> :
          user.data.role === 'buyer' ? <BuyerWorkspace transactions={transactions.data ?? []} lots={lots.data ?? []} onRespond={respond} onDone={reload} onError={setNotice} /> :
            <div className="state-card error-state"><CircleHelp size={22} /><div><strong>এই পোর্টাল এখনো প্রস্তুত নয়</strong><p>Moderator, Authority ও Admin workflow পরবর্তী বাস্তবায়ন ধাপে রয়েছে।</p></div></div>}
      </main>
    </div>
  )
}

function FarmerWorkspace({ buyers, transactions, onDone, onError }: { buyers: Buyer[]; transactions: Transaction[]; onDone: () => Promise<void>; onError: (message: string) => void }) {
  const mutation = useMutation({
    mutationFn: (values: Record<string, string>) => api('/transactions', { method: 'POST', body: JSON.stringify(values) }),
    onSuccess: async () => { onError('বিক্রির তথ্য জমা হয়েছে। ক্রেতার নিশ্চিতকরণের অপেক্ষায় আছে।'); await onDone() },
    onError: (error) => onError(error instanceof Error ? error.message : 'লেনদেন জমা দেওয়া যায়নি'),
  })
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const values = Object.fromEntries(new FormData(event.currentTarget).entries()) as Record<string, string>
    mutation.mutate(values)
    event.currentTarget.reset()
  }
  return <div className="workspace-grid">
    <section className="content-card">
      <div className="card-title-row"><div><h2>বিক্রির তথ্য জমা দিন</h2><p>ক্রেতা নিশ্চিত না করা পর্যন্ত এটি যাচাইকৃত নয়।</p></div><span className="card-title-icon"><Wheat size={19} /></span></div>
      {!buyers.length && <div className="inline-warning">এখনো কোনো ক্রেতা অ্যাকাউন্ট নেই। ক্রেতাকে আগে নিবন্ধন করতে বলুন।</div>}
      <form className="form-stack compact-form" onSubmit={submit}>
        <label>ক্রেতা<select name="buyer_id" required defaultValue=""><option value="" disabled>ক্রেতা নির্বাচন করুন</option>{buyers.map((buyer) => <option value={buyer.id} key={buyer.id}>{buyer.name}</option>)}</select></label>
        <div className="form-row"><label>পরিমাণ (কেজি)<input name="quantity_kg" type="number" step="0.001" min="0.001" required /></label><label>দাম / কেজি (৳)<input name="price_per_kg" type="number" step="0.01" min="0.01" required /></label></div>
        <div className="form-row"><label>জেলা<input name="district" defaultValue="Faridpur" required /></label><label>উপজেলা<input name="upazila" defaultValue="Faridpur Sadar" required /></label></div>
        <label>বিক্রির তারিখ<input name="sale_date" type="date" defaultValue={TODAY} required /></label>
        <button className="button button-primary button-full" disabled={!buyers.length || mutation.isPending}>লেনদেন জমা দিন <ArrowRight size={16} /></button>
      </form>
    </section>
    <TransactionList transactions={transactions} />
  </div>
}

function BuyerWorkspace({ transactions, lots, onRespond, onDone, onError }: { transactions: Transaction[]; lots: Lot[]; onRespond: (id: string, confirm: boolean) => void; onDone: () => Promise<void>; onError: (message: string) => void }) {
  return <div className="buyer-sections">
    <section className="content-card">
      <div className="card-title-row"><div><h2>ক্রেতার নিশ্চিতকরণ</h2><p>তথ্য যাচাই করে নিশ্চিত করুন অথবা কারণসহ বিরোধ জানান।</p></div><span className="card-title-icon"><ClipboardCheck size={19} /></span></div>
      <div className="confirm-list">{transactions.filter((item) => item.status === 'pending').map((item) => <div className="confirm-card" key={item.id}><div className="confirm-info"><span className="crop-icon"><Wheat size={19} /></span><div><strong>{Number(item.quantity_kg).toLocaleString()} কেজি {item.crop === 'onion' ? 'পেঁয়াজ' : item.crop}</strong><small>৳{Number(item.price_per_kg).toFixed(2)}/কেজি · {item.upazila}, {item.district}</small></div></div><div className="confirm-actions"><button className="button button-outline button-small" onClick={() => onRespond(item.id, false)}>বিরোধ জানান</button><button className="button button-primary button-small" onClick={() => onRespond(item.id, true)}><Check size={15} /> নিশ্চিত করুন</button></div></div>)}
      {!transactions.some((item) => item.status === 'pending') && <p className="empty-note">নতুন কোনো নিশ্চিতকরণের অনুরোধ নেই।</p>}</div>
    </section>
    <section className="content-card">
      <div className="card-title-row"><div><h2>মজুত ও লট</h2><p>মজুতের পরিবর্তনগুলো যাচাইযোগ্যভাবে নথিভুক্ত হয়।</p></div><span className="card-title-icon"><PackageCheck size={19} /></span></div>
      {!lots.length && <p className="empty-note">ক্রেতা নিশ্চিত করলে এখানে লট দেখা যাবে।</p>}
      <div className="lot-list">{lots.map((lot) => <LotCard key={lot.id} lot={lot} onDone={onDone} onError={onError} />)}</div>
    </section>
    <TransactionList transactions={transactions} />
  </div>
}

function LotCard({ lot, onDone, onError }: { lot: Lot; onDone: () => Promise<void>; onError: (message: string) => void }) {
  const [amount, setAmount] = useState('')
  const [purpose, setPurpose] = useState('storage')
  const [location, setLocation] = useState('')
  const [date, setDate] = useState('')
  async function declare(event: FormEvent) {
    event.preventDefault()
    try {
      await api(`/inventory/lots/${lot.id}/declaration`, { method: 'POST', body: JSON.stringify({ purpose, storage_location: location, expected_release_date: date }) })
      onError('মজুতের ঘোষণা সংরক্ষিত হয়েছে।')
      await onDone()
    } catch (error) { onError(error instanceof Error ? error.message : 'ঘোষণা সংরক্ষণ করা যায়নি') }
  }
  async function release() {
    try {
      await api(`/inventory/lots/${lot.id}/movements`, { method: 'POST', body: JSON.stringify({ movement_type: 'release', quantity_kg: amount }) })
      setAmount('')
      onError('মজুত ছাড়ের তথ্য নথিভুক্ত হয়েছে।')
      await onDone()
    } catch (error) { onError(error instanceof Error ? error.message : 'মজুত ছাড় নথিভুক্ত করা যায়নি') }
  }
  return <article className="lot-card"><div className="lot-top"><span className="crop-icon"><PackageCheck size={18} /></span><div><strong>যাচাইকৃত লট</strong><small>{lot.id.slice(0, 8)}… · {lot.crop}</small></div><span className="lot-quantity">{Number(lot.remaining_quantity_kg).toLocaleString()} কেজি</span></div>
    {!lot.purpose ? <form className="declaration-form" onSubmit={declare}><strong>মজুতের ঘোষণা প্রয়োজন</strong><div className="form-row"><label>উদ্দেশ্য<select value={purpose} onChange={(event) => setPurpose(event.target.value)}><option value="storage">সংরক্ষণ</option><option value="resale">পুনর্বিক্রয়</option><option value="wholesale">পাইকারি বিতরণ</option><option value="processing">প্রক্রিয়াজাতকরণ</option><option value="other">অন্যান্য</option></select></label><label>প্রত্যাশিত ছাড়ের তারিখ<input type="date" value={date} onChange={(event) => setDate(event.target.value)} required min={TODAY} /></label></div><label>গুদামের অবস্থান<input value={location} onChange={(event) => setLocation(event.target.value)} required minLength={2} /></label><button className="button button-primary button-small">ঘোষণা সংরক্ষণ <ArrowRight size={14} /></button></form>
      : <div className="lot-declared"><span><Check size={14} /> {lot.purpose} · {lot.storage_location}</span><small>প্রত্যাশিত ছাড়: {lot.expected_release_date?.slice(0, 10)}</small><div className="release-row"><input type="number" min="0.001" max={lot.remaining_quantity_kg} step="0.001" value={amount} onChange={(event) => setAmount(event.target.value)} placeholder="ছাড়ের পরিমাণ (কেজি)" /><button className="button button-outline button-small" disabled={!amount} onClick={release}>মজুত ছাড়</button></div></div>}
  </article>
}

function TransactionList({ transactions }: { transactions: Transaction[] }) {
  const statusLabel: Record<string, string> = { pending: 'অপেক্ষমাণ', confirmed: 'নিশ্চিত', disputed: 'বিরোধপূর্ণ', unconfirmed: 'অনিশ্চিত' }
  return <section className="content-card transaction-card"><div className="card-title-row"><div><h2>সাম্প্রতিক লেনদেন</h2><p>আপনার জমা দেওয়া ও পাওয়া লেনদেন</p></div><span className="card-title-icon"><ClipboardCheck size={19} /></span></div>
    {!transactions.length ? <p className="empty-note">এখনো কোনো লেনদেন নেই।</p> : <div className="table-scroll"><table><thead><tr><th>ফসল / তারিখ</th><th>পরিমাণ</th><th>দাম / কেজি</th><th>অবস্থা</th></tr></thead><tbody>{transactions.map((item) => <tr key={item.id}><td><strong>{item.crop === 'onion' ? 'পেঁয়াজ' : item.crop}</strong><small>{item.sale_date.slice(0, 10)}</small></td><td>{Number(item.quantity_kg).toLocaleString()} কেজি</td><td>৳{Number(item.price_per_kg).toFixed(2)}</td><td><span className={`status-pill status-${item.status}`}>{statusLabel[item.status] ?? item.status}</span></td></tr>)}</tbody></table></div>}
  </section>
}

function SiteFooter() {
  return <footer className="site-footer"><div className="container footer-inner"><Brand inverse /><span>ন্যায্য দাম, স্বচ্ছ হাট।</span><span className="footer-note">ডেমো পরিবেশ · সব সিমুলেটেড তথ্য স্পষ্টভাবে চিহ্নিত</span><span>© SwachchhoHat</span></div></footer>
}

function Root() {
  return <App />
}

export default function AppRoot() {
  return <Root />
}
