--
-- PostgreSQL database dump
--

-- Dumped from database version 16.4
-- Dumped by pg_dump version 16.3

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: accounts; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.accounts (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    industry character varying(50) NOT NULL,
    website character varying(120) NOT NULL,
    created_at timestamp without time zone NOT NULL,
    user_id integer NOT NULL
);


ALTER TABLE public.accounts OWNER TO neondb_owner;

--
-- Name: accounts_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.accounts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.accounts_id_seq OWNER TO neondb_owner;

--
-- Name: accounts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.accounts_id_seq OWNED BY public.accounts.id;


--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


ALTER TABLE public.alembic_version OWNER TO neondb_owner;

--
-- Name: emails; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.emails (
    id integer NOT NULL,
    sender character varying(255) NOT NULL,
    subject character varying(255) NOT NULL,
    content text NOT NULL,
    received_at timestamp without time zone NOT NULL,
    lead_id integer NOT NULL
);


ALTER TABLE public.emails OWNER TO neondb_owner;

--
-- Name: emails_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.emails_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.emails_id_seq OWNER TO neondb_owner;

--
-- Name: emails_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.emails_id_seq OWNED BY public.emails.id;


--
-- Name: leads; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.leads (
    id integer NOT NULL,
    name character varying(100) NOT NULL,
    email character varying(120) NOT NULL,
    phone character varying(20) NOT NULL,
    status character varying(20) NOT NULL,
    created_at timestamp without time zone NOT NULL,
    last_contact timestamp without time zone NOT NULL,
    last_followup_email timestamp without time zone,
    last_followup_tracking_id character varying(36),
    last_email_opened timestamp without time zone,
    user_id integer NOT NULL,
    score double precision NOT NULL
);


ALTER TABLE public.leads OWNER TO neondb_owner;

--
-- Name: leads_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.leads_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.leads_id_seq OWNER TO neondb_owner;

--
-- Name: leads_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.leads_id_seq OWNED BY public.leads.id;


--
-- Name: opportunities; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.opportunities (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    amount double precision NOT NULL,
    stage character varying(50) NOT NULL,
    close_date timestamp without time zone NOT NULL,
    created_at timestamp without time zone NOT NULL,
    user_id integer NOT NULL,
    account_id integer NOT NULL,
    lead_id integer
);


ALTER TABLE public.opportunities OWNER TO neondb_owner;

--
-- Name: opportunities_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.opportunities_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.opportunities_id_seq OWNER TO neondb_owner;

--
-- Name: opportunities_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.opportunities_id_seq OWNED BY public.opportunities.id;


--
-- Name: schedules; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.schedules (
    id integer NOT NULL,
    title character varying(255) NOT NULL,
    description text NOT NULL,
    start_time timestamp without time zone NOT NULL,
    end_time timestamp without time zone NOT NULL,
    user_id integer NOT NULL,
    account_id integer,
    lead_id integer,
    opportunity_id integer
);


ALTER TABLE public.schedules OWNER TO neondb_owner;

--
-- Name: schedules_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.schedules_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.schedules_id_seq OWNER TO neondb_owner;

--
-- Name: schedules_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.schedules_id_seq OWNED BY public.schedules.id;


--
-- Name: tasks; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.tasks (
    id integer NOT NULL,
    title character varying(255) NOT NULL,
    description text NOT NULL,
    due_date timestamp without time zone NOT NULL,
    completed boolean NOT NULL,
    created_at timestamp without time zone NOT NULL,
    user_id integer NOT NULL,
    lead_id integer,
    opportunity_id integer,
    account_id integer
);


ALTER TABLE public.tasks OWNER TO neondb_owner;

--
-- Name: tasks_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.tasks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tasks_id_seq OWNER TO neondb_owner;

--
-- Name: tasks_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.tasks_id_seq OWNED BY public.tasks.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(255) NOT NULL,
    email character varying(255) NOT NULL,
    password_hash character varying(512) NOT NULL,
    role character varying(20) NOT NULL
);


ALTER TABLE public.users OWNER TO neondb_owner;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO neondb_owner;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: accounts id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.accounts ALTER COLUMN id SET DEFAULT nextval('public.accounts_id_seq'::regclass);


--
-- Name: emails id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.emails ALTER COLUMN id SET DEFAULT nextval('public.emails_id_seq'::regclass);


--
-- Name: leads id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.leads ALTER COLUMN id SET DEFAULT nextval('public.leads_id_seq'::regclass);


--
-- Name: opportunities id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.opportunities ALTER COLUMN id SET DEFAULT nextval('public.opportunities_id_seq'::regclass);


--
-- Name: schedules id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.schedules ALTER COLUMN id SET DEFAULT nextval('public.schedules_id_seq'::regclass);


--
-- Name: tasks id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.tasks ALTER COLUMN id SET DEFAULT nextval('public.tasks_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: accounts; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.accounts (id, name, industry, website, created_at, user_id) FROM stdin;
1	西尾システムコンサルタント	サービス業	https://www.team240.net	2024-09-23 20:46:30.747749	1
\.


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.alembic_version (version_num) FROM stdin;
c5dace7740a7
\.


--
-- Data for Name: emails; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.emails (id, sender, subject, content, received_at, lead_id) FROM stdin;
1	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/07/21 10:24に注文いただいたエクセルシア原当麻　無線LAN導入のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/07/21 10:24に注文いただいたエクセルシア原当麻　無線LAN導入のお客様に連絡する\r\n期限: 2020/04/16\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 13:35:27.913126	3
2	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/07/21 10:54に注文いただいたコンテックス堀田さんPC　購入のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/07/21 10:54に注文いただいたコンテックス堀田さんPC　購入のお客様に連絡する\r\n期限: 2020/04/16\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 13:35:31.525909	3
3	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：黒川さん解約)	タスクが割り当てられました。\r\n 真言 西尾様,\r\n \r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: &#x9ed2;&#x5ddd;&#x3055;&#x3093;&#x89e3;&#x7d04;\r\n期限: 2017/07/31\r\n\r\nよろしくお願いします,\r\n真言 西尾	2024-09-24 13:46:05.923898	3
4	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/07/30 12:41に注文いただいた大丸製作所 外付けHDDのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/07/30 12:41に注文いただいた大丸製作所 外付けHDDのお客様に連絡する\r\n期限: 2020/04/25\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 13:46:21.74957	3
5	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/07/21 10:54に注文いただいたコンテックス堀田さんPC 購入のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/07/21 10:54に注文いただいたコンテックス堀田さんPC 購入のお客様に連絡する\r\n期限: 2020/04/16\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 13:46:25.968405	3
6	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/07/30 12:41に注文いただいた大丸製作所 外付けHDDのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/07/30 12:41に注文いただいた大丸製作所 外付けHDDのお客様に連絡する\r\n期限: 2020/04/25\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 13:50:03.907467	3
7	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/07/30 12:41に注文いただいた大丸製作所 外付けHDDのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/07/30 12:41に注文いただいた大丸製作所 外付けHDDのお客様に連絡する\r\n期限: 2020/04/25\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 13:50:14.96544	3
8	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/08/08 21:23に注文いただいたおおさわ 月間IT化＆デザインのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/08/08 21:23に注文いただいたおおさわ 月間IT化＆デザインのお客様に連絡する\r\n期限: 2020/05/04\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 13:55:20.814328	3
9	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/08/13 20:33に注文いただいた金子さんのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/08/13 20:33に注文いただいた金子さんのお客様に連絡する\r\n期限: 2020/05/09\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 14:09:51.850217	3
10	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/08/13 20:33に注文いただいた金子さんのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/08/13 20:33に注文いただいた金子さんのお客様に連絡する\r\n期限: 2020/05/09\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 14:09:59.184774	3
11	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/08/24 14:42に注文いただいた中塚富士通ノート起動しない。のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/08/24 14:42に注文いただいた中塚富士通ノート起動しない。のお客様に連絡する\r\n期限: 2020/05/20\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 14:35:20.603514	3
12	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/06/08 09:35に注文いただいた仲正さんNAS導入のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/06/08 09:35に注文いただいた仲正さんNAS導入のお客様に連絡する\r\n期限: 2020/03/04\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 14:35:25.611114	3
14	makoto@team240.net	Re: Fwd: SMS Magic Registration Successful - 80010380	Hi care,\r\nI&#39;ll give you below information\r\nOfficial email id                              makoto@team240.net Office phone number                   +81427763696Company Registration Id and       No ID in JapanTax ID\r\n\r\n有限会社西尾システムコンサルタント 代表取締役　西尾真言携帯090-7176-1549フリーダイヤル0120-240-542\r\n\r\n---- 2017/09/08 12:02 care@screen-magic.com wrote ----\r\n\r\n    Hi Makoto, \r\n Thank you for choosing SMS Magic. I have received your request for the account activation and I need your help with the same. Can you also provide us below details for verification purposes:   Official email id \r\n Office phone number \r\n Company Registration Id and \r\n Tax ID\r\n  Also, I&#39;d suggest you reply with your official Email address so that I can help you in a better way.   Awaiting your response. \r\n    Regards, Dipali Shelar Sr. Customer Success Engineer Screen Magic Mobile Media Pvt. Ltd. \r\n Toll Free - US: 1-888-568-1315 | UK: 0-808-189-1305 | AUS: 1-800-823-175 | IND (Toll) : +91-20-65200192 | skype: support.sms-magic | email:care@screen-magic.com | web: www.screen-magic.com | support hours: Mon to Fri ( 2 am to 10 pm GMT ) ============================================================================= Not happy with the progress of this ticket ? Have any other concerns or complaints ? Write immediately to escalations@screen-magic.com so that we can make things right.  Our customers are at the heart of our business and we are committed to giving them the highest quality service every time.    =============================================================================     \r\n 54505:10575\r\n	2024-09-24 15:24:51.688697	3
16	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/09/19 14:16に注文いただいたIPAD PRO　購入のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/09/19 14:16に注文いただいたIPAD PRO　購入のお客様に連絡する\r\n期限: 2020/06/15\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:25:34.989543	3
13	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/09/04 10:40に注文いただいた木村　NEC pc-ll700fd電源入らないのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/09/04 10:40に注文いただいた木村　NEC pc-ll700fd電源入らないのお客様に連絡する\r\n期限: 2020/05/31\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:04:32.127172	3
15	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/06/08 09:35に注文いただいた仲正さんNAS導入のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/06/08 09:35に注文いただいた仲正さんNAS導入のお客様に連絡する\r\n期限: 2020/03/04\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:25:05.917128	3
17	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/09/19 14:16に注文いただいたIPAD PRO　購入のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/09/19 14:16に注文いただいたIPAD PRO　購入のお客様に連絡する\r\n期限: 2020/06/15\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:29:16.289142	3
18	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/09/04 10:40に注文いただいた木村　NEC pc-ll700fd電源入らないのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/09/04 10:40に注文いただいた木村　NEC pc-ll700fd電源入らないのお客様に連絡する\r\n期限: 2020/05/31\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:35:08.255553	3
19	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/09/27 13:35に注文いただいた青木社労士事務所　ドットプリンタでないのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/09/27 13:35に注文いただいた青木社労士事務所　ドットプリンタでないのお客様に連絡する\r\n期限: 2020/06/23\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:35:21.007484	3
20	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/09/30 06:23に注文いただいた安田さん外付けthunderbolt SSD 500Gのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/09/30 06:23に注文いただいた安田さん外付けthunderbolt SSD 500Gのお客様に連絡する\r\n期限: 2020/06/26\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:35:27.684855	3
21	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：クラフト点検打合せ)	タスクが割り当てられました。\r\n 真言 西尾様,\r\n \r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: &#x30af;&#x30e9;&#x30d5;&#x30c8;&#x70b9;&#x691c;&#x6253;&#x5408;&#x305b;\r\n期限: 2017/10/02\r\n\r\nよろしくお願いします,\r\n真言 西尾	2024-09-24 15:35:33.700187	3
22	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/09/30 06:23に注文いただいた安田さん外付けthunderbolt SSD 500Gのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/09/30 06:23に注文いただいた安田さん外付けthunderbolt SSD 500Gのお客様に連絡する\r\n期限: 2020/06/26\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:35:35.526239	3
23	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/10/06 10:18に注文いただいたラムダプレシジョンNAS導入のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/10/06 10:18に注文いただいたラムダプレシジョンNAS導入のお客様に連絡する\r\n期限: 2020/07/02\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:35:53.375009	3
24	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/09/27 17:46に注文いただいた山本　DVD復旧作業のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/09/27 17:46に注文いただいた山本　DVD復旧作業のお客様に連絡する\r\n期限: 2020/06/23\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:35:58.002346	3
25	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/10/04 13:28に注文いただいた大丸製作所 sony 画面真っ黒のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/10/04 13:28に注文いただいた大丸製作所 sony 画面真っ黒のお客様に連絡する\r\n期限: 2020/06/30\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:36:01.656583	3
26	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/09/30 06:23に注文いただいた安田さん外付けthunderbolt SSD 500Gのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/09/30 06:23に注文いただいた安田さん外付けthunderbolt SSD 500Gのお客様に連絡する\r\n期限: 2020/06/26\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:36:04.73187	3
28	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/10/12 18:57に注文いただいた佐伯 DELL PRECISION T7500 HDD故障のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/10/12 18:57に注文いただいた佐伯 DELL PRECISION T7500 HDD故障のお客様に連絡する\r\n期限: 2020/07/08\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:36:28.796466	3
30	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/10/12 18:57に注文いただいた佐伯 DELL PRECISION T7500 HDD故障のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/10/12 18:57に注文いただいた佐伯 DELL PRECISION T7500 HDD故障のお客様に連絡する\r\n期限: 2020/07/08\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:36:58.738707	3
32	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/10/25 09:33に注文いただいた柴田　ウィルス感染のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/10/25 09:33に注文いただいた柴田　ウィルス感染のお客様に連絡する\r\n期限: 2020/07/21\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:37:16.066316	3
34	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/10/20 09:22に注文いただいた飯島パソコン不具合のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/10/20 09:22に注文いただいた飯島パソコン不具合のお客様に連絡する\r\n期限: 2020/07/16\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:37:22.102635	3
36	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/10/20 09:22に注文いただいた飯島パソコン不具合のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/10/20 09:22に注文いただいた飯島パソコン不具合のお客様に連絡する\r\n期限: 2020/07/16\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:37:29.376131	3
38	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/10/23 14:08に注文いただいた岡田 小山　DELL買い替えのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/10/23 14:08に注文いただいた岡田 小山　DELL買い替えのお客様に連絡する\r\n期限: 2020/07/19\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:37:44.193528	3
40	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：請求期限日到来)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 請求期限日到来\r\n期限: 2017/11/09\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:38:11.279941	3
42	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：請求期限日到来)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 請求期限日到来\r\n期限: 2017/11/12\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:38:24.221753	3
44	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/11/19 16:53に注文いただいたおおさわ 月間IT化＆デザインのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/11/19 16:53に注文いただいたおおさわ 月間IT化＆デザインのお客様に連絡する\r\n期限: 2020/08/15\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:38:51.773653	3
46	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/11/20 10:49に注文いただいた鈴木實　パソコン買い換え相談のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/11/20 10:49に注文いただいた鈴木實　パソコン買い換え相談のお客様に連絡する\r\n期限: 2020/08/16\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:39:03.409635	3
27	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：河野さんに電話)	タスクが割り当てられました。\r\n 真言 西尾様,\r\n \r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: &#x6cb3;&#x91ce;&#x3055;&#x3093;&#x306b;&#x96fb;&#x8a71;\r\n期限: 2017/10/12\r\n\r\nよろしくお願いします,\r\n真言 西尾	2024-09-24 15:36:22.305531	3
29	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/10/12 18:57に注文いただいた佐伯 DELL PRECISION T7500 HDD故障のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/10/12 18:57に注文いただいた佐伯 DELL PRECISION T7500 HDD故障のお客様に連絡する\r\n期限: 2020/07/08\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:36:41.407087	3
31	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/10/25 09:33に注文いただいた柴田　ウィルス感染のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/10/25 09:33に注文いただいた柴田　ウィルス感染のお客様に連絡する\r\n期限: 2020/07/21\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:37:12.416488	3
33	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/10/20 09:22に注文いただいた飯島パソコン不具合のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/10/20 09:22に注文いただいた飯島パソコン不具合のお客様に連絡する\r\n期限: 2020/07/16\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:37:19.707496	3
35	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/10/20 09:20に注文いただいた菊地博　パソコン不具合　修理または買い替えのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/10/20 09:20に注文いただいた菊地博　パソコン不具合　修理または買い替えのお客様に連絡する\r\n期限: 2020/07/16\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:37:24.519214	3
37	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/10/20 09:22に注文いただいた飯島パソコン不具合のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/10/20 09:22に注文いただいた飯島パソコン不具合のお客様に連絡する\r\n期限: 2020/07/16\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:37:36.962905	3
39	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/09/30 06:23に注文いただいた安田さん外付けthunderbolt SSD 500Gのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/09/30 06:23に注文いただいた安田さん外付けthunderbolt SSD 500Gのお客様に連絡する\r\n期限: 2020/06/26\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:37:47.202375	3
41	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/10/23 14:08に注文いただいた岡田 小山　DELL買い替えのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/10/23 14:08に注文いただいた岡田 小山　DELL買い替えのお客様に連絡する\r\n期限: 2020/07/19\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:38:13.873801	3
43	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/11/16 18:24に注文いただいた井関 vista PC 買い替えのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/11/16 18:24に注文いただいた井関 vista PC 買い替えのお客様に連絡する\r\n期限: 2020/08/12\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:38:39.953937	3
45	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/11/19 16:55に注文いただいたおおさわ 月間IT化＆デザインのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/11/19 16:55に注文いただいたおおさわ 月間IT化＆デザインのお客様に連絡する\r\n期限: 2020/08/15\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:38:57.922989	3
47	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/11/20 10:49に注文いただいた鈴木實　パソコン買い換え相談のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/11/20 10:49に注文いただいた鈴木實　パソコン買い換え相談のお客様に連絡する\r\n期限: 2020/08/16\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:39:05.806519	3
48	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：堀田さんのパソコン\n\nバックアップはこれでqnapにとっています)	タスクが割り当てられました。\r\n 真言 西尾様,\r\n \r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: &#x5800;&#x7530;&#x3055;&#x3093;&#x306e;&#x30d1;&#x30bd;&#x30b3;&#x30f3; &#x30d0;&#x30c3;&#x30af;&#x30a2;&#x30c3;&#x30d7;&#x306f;&#x3053;&#x308c;&#x3067;qnap&#x306b;&#x3068;&#x3063;&#x3066;&#x3044;&#x307e;&#x3059;\r\n期限: 2017/11/22\r\n\r\nよろしくお願いします,\r\n真言 西尾	2024-09-24 15:39:08.852146	3
50	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/11/20 10:49に注文いただいた鈴木實　パソコン買い換え相談のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/11/20 10:49に注文いただいた鈴木實　パソコン買い換え相談のお客様に連絡する\r\n期限: 2020/08/16\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:39:14.314886	3
52	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/11/16 18:24に注文いただいた井関 vista PC 買い替えのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/11/16 18:24に注文いただいた井関 vista PC 買い替えのお客様に連絡する\r\n期限: 2020/08/12\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:39:20.503619	3
54	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/11/20 12:03に注文いただいた小倉　中古PC探す　office必要のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/11/20 12:03に注文いただいた小倉　中古PC探す　office必要のお客様に連絡する\r\n期限: 2020/08/16\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:39:41.264631	3
56	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/09/29 15:23に注文いただいた黒川さんSONYノートバッテリ交換VGP-BPL19のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/09/29 15:23に注文いただいた黒川さんSONYノートバッテリ交換VGP-BPL19のお客様に連絡する\r\n期限: 2020/06/25\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:39:58.768416	3
58	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/06/08 09:35に注文いただいた仲正さんNAS導入のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/06/08 09:35に注文いただいた仲正さんNAS導入のお客様に連絡する\r\n期限: 2020/03/04\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:40:31.812797	3
60	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/12/13 15:12に注文いただいたTOCO東久留米 無線LAN導入のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/12/13 15:12に注文いただいたTOCO東久留米 無線LAN導入のお客様に連絡する\r\n期限: 2020/09/08\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:40:39.066914	3
62	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：請求期限日到来)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 請求期限日到来\r\n期限: 2017/12/14\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:40:47.610277	3
49	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/11/20 10:49に注文いただいた鈴木實　パソコン買い換え相談のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/11/20 10:49に注文いただいた鈴木實　パソコン買い換え相談のお客様に連絡する\r\n期限: 2020/08/16\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:39:11.254762	3
51	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/11/16 18:24に注文いただいた井関 vista PC 買い替えのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/11/16 18:24に注文いただいた井関 vista PC 買い替えのお客様に連絡する\r\n期限: 2020/08/12\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:39:18.696569	3
53	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/11/20 12:03に注文いただいた小倉　中古PC探す　office必要のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/11/20 12:03に注文いただいた小倉　中古PC探す　office必要のお客様に連絡する\r\n期限: 2020/08/16\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:39:24.712812	3
55	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/11/20 12:03に注文いただいた小倉　中古PC探す　office必要のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/11/20 12:03に注文いただいた小倉　中古PC探す　office必要のお客様に連絡する\r\n期限: 2020/08/16\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:39:53.026828	3
57	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/09/29 15:23に注文いただいた黒川さんSONYノートバッテリ交換VGP-BPL19のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/09/29 15:23に注文いただいた黒川さんSONYノートバッテリ交換VGP-BPL19のお客様に連絡する\r\n期限: 2020/06/25\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:40:02.402748	3
59	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/08/24 14:42に注文いただいた中塚富士通ノート起動しない。のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/08/24 14:42に注文いただいた中塚富士通ノート起動しない。のお客様に連絡する\r\n期限: 2020/05/20\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:40:35.409129	3
61	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/12/13 15:12に注文いただいたTOCO東久留米 無線LAN導入のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/12/13 15:12に注文いただいたTOCO東久留米 無線LAN導入のお客様に連絡する\r\n期限: 2020/09/08\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:40:42.67946	3
63	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/12/14 11:08に注文いただいた相模理工 サーバー繋がないのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/12/14 11:08に注文いただいた相模理工 サーバー繋がないのお客様に連絡する\r\n期限: 2020/09/09\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:40:52.083848	3
64	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/12/14 11:08に注文いただいた相模理工 サーバー繋がないのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/12/14 11:08に注文いただいた相模理工 サーバー繋がないのお客様に連絡する\r\n期限: 2020/09/09\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:40:56.339921	3
65	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/12/16 18:08に注文いただいたビオラ デッスクPC買い換え 予算200000のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/12/16 18:08に注文いただいたビオラ デッスクPC買い換え 予算200000のお客様に連絡する\r\n期限: 2020/09/11\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:41:04.702184	3
66	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/12/16 18:08に注文いただいたビオラ デッスクPC買い換えのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/12/16 18:08に注文いただいたビオラ デッスクPC買い換えのお客様に連絡する\r\n期限: 2020/09/11\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:41:07.72831	3
68	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/09/26 16:51に注文いただいた第五回訴訟団 WEB相談のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/09/26 16:51に注文いただいた第五回訴訟団 WEB相談のお客様に連絡する\r\n期限: 2020/06/22\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:41:19.872734	3
70	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/12/19 16:10に注文いただいた（株）おおさわ　メインPC　新規交換のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/12/19 16:10に注文いただいた（株）おおさわ　メインPC　新規交換のお客様に連絡する\r\n期限: 2020/09/14\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:41:32.704389	3
72	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/09/26 16:51に注文いただいた第五次訴訟団 WEB相談のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/09/26 16:51に注文いただいた第五次訴訟団 WEB相談のお客様に連絡する\r\n期限: 2020/06/22\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:41:44.316348	3
74	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/12/26 22:05に注文いただいた伊藤一周電設パソコン買い替えのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/12/26 22:05に注文いただいた伊藤一周電設パソコン買い替えのお客様に連絡する\r\n期限: 2020/09/21\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:42:07.814028	3
76	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/11/20 12:03に注文いただいた小倉　中古PC探す　office必要のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/11/20 12:03に注文いただいた小倉　中古PC探す　office必要のお客様に連絡する\r\n期限: 2020/08/16\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:42:20.969497	3
78	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/12/19 16:10に注文いただいた（株）おおさわ　メインPC　新規交換のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/12/19 16:10に注文いただいた（株）おおさわ　メインPC　新規交換のお客様に連絡する\r\n期限: 2020/09/14\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:42:27.036303	3
80	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/01/12 19:28に注文いただいた大石　TOSHIBA一体型DT73/V9HB　HDD故障のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/01/12 19:28に注文いただいた大石　TOSHIBA一体型DT73/V9HB　HDD故障のお客様に連絡する\r\n期限: 2020/10/08\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:43:02.971709	3
82	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2016/09/13 20:57に注文いただいた訪問：白井 Officeと弥生会計買う★2016/03/30 PM6のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2016/09/13 20:57に注文いただいた訪問：白井 Officeと弥生会計買う★2016/03/30 PM6のお客様に連絡する\r\n期限: 2019/06/10\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:43:13.242772	3
84	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2016/09/13 20:57に注文いただいた訪問：白井 Officeと弥生会計買う★2016/03/30 PM6のお客様に連絡する)	タスクが割り当てられました。\r\n 真言 西尾様,\r\n \r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: &#x8cb7;&#x66ff;&#x30fb;&#x4e0d;&#x5177;&#x5408;&#x70b9;&#x691c;&#x3092;&#x304a;&#x5ba2;&#x69d8;&#x306b;PUSH&#x3059;&#x308b;&#x3002;2016&#x2f;09&#x2f;13 20&#x3a;57&#x306b;&#x6ce8;&#x6587;&#x3044;&#x305f;&#x3060;&#x3044;&#x305f;&#x8a2a;&#x554f;&#xff1a;&#x767d;&#x4e95; Office&#x3068;&#x5f25;&#x751f;&#x4f1a;&#x8a08;&#x8cb7;&#x3046;&#x2605;2016&#x2f;03&#x2f;30 PM6&#x306e;&#x304a;&#x5ba2;&#x69d8;&#x306b;&#x9023;&#x7d61;&#x3059;&#x308b;\r\n期限: 2019/06/10\r\n\r\nよろしくお願いします,\r\n真言 西尾	2024-09-24 15:43:19.282232	3
67	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/12/16 20:50に注文いただいたおおさわ 月間IT化＆デザインのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/12/16 20:50に注文いただいたおおさわ 月間IT化＆デザインのお客様に連絡する\r\n期限: 2020/09/11\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:41:13.205232	3
69	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/09/30 06:23に注文いただいた安田さん外付けthunderbolt SSD 500Gのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/09/30 06:23に注文いただいた安田さん外付けthunderbolt SSD 500Gのお客様に連絡する\r\n期限: 2020/06/26\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:41:24.097495	3
71	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/09/26 16:51に注文いただいた第五次訴訟団 WEB相談のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/09/26 16:51に注文いただいた第五次訴訟団 WEB相談のお客様に連絡する\r\n期限: 2020/06/22\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:41:41.92994	3
73	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/12/16 18:08に注文いただいたビオラ デッスクPC買い換えのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/12/16 18:08に注文いただいたビオラ デッスクPC買い換えのお客様に連絡する\r\n期限: 2020/09/11\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:41:47.349357	3
75	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/12/16 18:08に注文いただいたビオラ デッスクPC買い換えのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/12/16 18:08に注文いただいたビオラ デッスクPC買い換えのお客様に連絡する\r\n期限: 2020/09/11\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:42:12.064961	3
77	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/12/13 15:12に注文いただいたTOCO東久留米 無線LAN導入のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/12/13 15:12に注文いただいたTOCO東久留米 無線LAN導入のお客様に連絡する\r\n期限: 2020/09/08\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:42:23.969489	3
79	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/12/26 22:05に注文いただいた伊藤一周電設パソコン買い替えのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/12/26 22:05に注文いただいた伊藤一周電設パソコン買い替えのお客様に連絡する\r\n期限: 2020/09/21\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:42:57.978269	3
81	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2016/09/13 20:57に注文いただいた訪問：白井 Officeと弥生会計買う★2016/03/30 PM6のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2016/09/13 20:57に注文いただいた訪問：白井 Officeと弥生会計買う★2016/03/30 PM6のお客様に連絡する\r\n期限: 2019/06/10\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:43:09.54496	3
83	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/10/06 10:18に注文いただいたラムダプレシジョンNAS導入のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/10/06 10:18に注文いただいたラムダプレシジョンNAS導入のお客様に連絡する\r\n期限: 2020/07/02\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:43:17.454727	3
85	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2016/09/13 20:57に注文いただいた訪問：白井 Officeと弥生会計買う★2016/03/30 PM6のお客様に連絡する)	タスクが割り当てられました。\r\n 真言 西尾様,\r\n \r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: &#x8cb7;&#x66ff;&#x30fb;&#x4e0d;&#x5177;&#x5408;&#x70b9;&#x691c;&#x3092;&#x304a;&#x5ba2;&#x69d8;&#x306b;PUSH&#x3059;&#x308b;&#x3002;2016&#x2f;09&#x2f;13 20&#x3a;57&#x306b;&#x6ce8;&#x6587;&#x3044;&#x305f;&#x3060;&#x3044;&#x305f;&#x8a2a;&#x554f;&#xff1a;&#x767d;&#x4e95; Office&#x3068;&#x5f25;&#x751f;&#x4f1a;&#x8a08;&#x8cb7;&#x3046;&#x2605;2016&#x2f;03&#x2f;30 PM6&#x306e;&#x304a;&#x5ba2;&#x69d8;&#x306b;&#x9023;&#x7d61;&#x3059;&#x308b;\r\n期限: 2019/06/10\r\n\r\nよろしくお願いします,\r\n真言 西尾	2024-09-24 15:43:21.113931	3
86	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/10/06 10:18に注文いただいたラムダプレシジョンNAS導入のお客様に連絡する)	タスクが割り当てられました。\r\n 真言 西尾様,\r\n \r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: &#x8cb7;&#x66ff;&#x30fb;&#x4e0d;&#x5177;&#x5408;&#x70b9;&#x691c;&#x3092;&#x304a;&#x5ba2;&#x69d8;&#x306b;PUSH&#x3059;&#x308b;&#x3002;2017&#x2f;10&#x2f;06 10&#x3a;18&#x306b;&#x6ce8;&#x6587;&#x3044;&#x305f;&#x3060;&#x3044;&#x305f;&#x30e9;&#x30e0;&#x30c0;&#x30d7;&#x30ec;&#x30b7;&#x30b8;&#x30e7;&#x30f3;NAS&#x5c0e;&#x5165;&#x306e;&#x304a;&#x5ba2;&#x69d8;&#x306b;&#x9023;&#x7d61;&#x3059;&#x308b;\r\n期限: 2020/07/02\r\n\r\nよろしくお願いします,\r\n真言 西尾	2024-09-24 15:43:22.967837	3
88	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/01/11 15:46に注文いただいた第五次　麻里子　会員管理PC買い換えのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/01/11 15:46に注文いただいた第五次　麻里子　会員管理PC買い換えのお客様に連絡する\r\n期限: 2020/10/07\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:43:58.920912	3
90	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/01/31 14:28に注文いただいた小高　一体型買い換え　NEC  VF-Sのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/01/31 14:28に注文いただいた小高　一体型買い換え　NEC VF-Sのお客様に連絡する\r\n期限: 2020/10/27\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:44:18.987491	3
92	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/01/31 21:07に注文いただいたおおさわ 月間IT化＆デザインのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/01/31 21:07に注文いただいたおおさわ 月間IT化＆デザインのお客様に連絡する\r\n期限: 2020/10/27\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:44:29.651675	3
94	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/02/15 00:09に注文いただいた白井20万円パソコンのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/02/15 00:09に注文いただいた白井20万円パソコンのお客様に連絡する\r\n期限: 2020/11/11\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:45:13.056719	3
96	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/03/04 13:25に注文いただいた夢ガレージ防犯カメラ 購入 wifiルータ交換のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/03/04 13:25に注文いただいた夢ガレージ防犯カメラ 購入 wifiルータ交換のお客様に連絡する\r\n期限: 2019/11/29\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:45:33.688195	3
98	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/03/26 14:47に注文いただいた飯田 さんバイオSSD交換のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/03/26 14:47に注文いただいた飯田 さんバイオSSD交換のお客様に連絡する\r\n期限: 2020/12/20\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:47:31.736871	3
100	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/04/10 14:42に注文いただいた薮田　買い換えのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/04/10 14:42に注文いただいた薮田　買い換えのお客様に連絡する\r\n期限: 2021/01/04\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:47:53.015694	3
102	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/04/20 17:08に注文いただいた伊藤亘さんavgと買い換え相談のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/04/20 17:08に注文いただいた伊藤亘さんavgと買い換え相談のお客様に連絡する\r\n期限: 2021/01/14\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:48:33.648497	3
104	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/04/20 19:14に注文いただいた郷原 PC買い替え→Lenovo ノートパソコン ideaPad 320 80XR009RJPのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/04/20 19:14に注文いただいた郷原 PC買い替え→Lenovo ノートパソコン ideaPad 320 80XR009RJPのお客様に連絡する\r\n期限: 2021/01/14\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:48:41.536558	3
87	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/01/11 15:46に注文いただいた第五次　麻里子　会員管理PC買い換えのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/01/11 15:46に注文いただいた第五次　麻里子　会員管理PC買い換えのお客様に連絡する\r\n期限: 2020/10/07\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:43:56.524629	3
89	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/12/16 18:08に注文いただいたビオラ 高機能デッスクPC買い換えのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/12/16 18:08に注文いただいたビオラ 高機能デッスクPC買い換えのお客様に連絡する\r\n期限: 2020/09/11\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:44:05.797308	3
91	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/01/31 14:28に注文いただいた小高　一体型買い換え→NEC PC-VK17EFWN4RNSのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/01/31 14:28に注文いただいた小高　一体型買い換え→NEC PC-VK17EFWN4RNSのお客様に連絡する\r\n期限: 2020/10/27\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:44:22.015366	3
93	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/02/07 15:49に注文いただいた西田　NEC PC-VK17EFWN4RNS 購入のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/02/07 15:49に注文いただいた西田　NEC PC-VK17EFWN4RNS 購入のお客様に連絡する\r\n期限: 2020/11/03\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:44:56.792993	3
95	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/02/15 00:09に注文いただいた白井20万円パソコンのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/02/15 00:09に注文いただいた白井20万円パソコンのお客様に連絡する\r\n期限: 2020/11/11\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:45:16.748221	3
97	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2016/09/13 20:57に注文いただいた大娘的店 飯田 さんバイオ修理2013/05/08 PM12のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2016/09/13 20:57に注文いただいた大娘的店 飯田 さんバイオ修理2013/05/08 PM12のお客様に連絡する\r\n期限: 2019/06/10\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:47:06.966441	3
99	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/04/10 14:42に注文いただいた薮田　買い換えのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/04/10 14:42に注文いただいた薮田　買い換えのお客様に連絡する\r\n期限: 2021/01/04\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:47:41.077705	3
101	makoto@team240.net	パソコン購入するならどっち？	   \r\n    \r\n      \r\n   \r\nパソコン購入するならどっち？ \r\n     \r\n    \r\n   \r\n\r\nMakoto 様 \r\nいつもパソコン修理でお世話になっております。  \r\nこんにちは 今回、安くパソコンを仕入れることが出来そうです。  \r\nそこでお客様にデスクトップとノートパソコンのどちらをご希望かお聞きしたいのです  \r\nこちらから  https://survey.zohopublic.com/zs/5lCu39 https://survey.zohopublic.com/zs/5lCu39 アンケートのお答えを参考に仕入したいと考えています。  \r\nお答えいただいた方を優先に販売を計画しております  \r\nよろしくお願いします  \r\n有限会社西尾システムコンサルタントの西尾真言です。  \r\n下記URLをタップするか、LINEまたはLINE WORKSで‘makoto@team240.com’をID検索して、アドレス帳に追加してください。\r\nhttps://works.do/R/ti/p/makoto@team240.com \r\n\r\n\r\nmakoto@team240.net      \r\n       \r\n \r\n    https://survey.zohopublic.com/zs/5lCu39   \r\n \r\n      \r\n      \r\n \r\n     http://$[ZS:SURVEYURL]$ Give Feedback               \r\n \r\n\r\n\r\n\r\n\r\n----------------------------------------------------------------------\r\nこのメールの送信者： makoto@team240.net 宛先 makoto@team240.net\r\n\r\n興味が無い場合登録の解除 - https://zcs1.maillist-manage.com/ua/optout?od=11287eca74936a&rd=1328fc21093b9533&sd=1328fc21093b94d5&n=124296dffbb2ec\r\n\r\n登録情報の更新 -  https://zcs1.maillist-manage.com/ua/upc?upd=1328fc21092c2209&r=1328fc21093b9533&n=124296dffbb2ec&od=11287eca74936a\r\n \r\n興味をお持ちの場合登録- https://zcs1.maillist-manage.com/ua/optin?od=11287eca74936a&rd=1328fc21093b9533&sd=1328fc21093b94d5&n=124296dffbb2ec\r\n \r\n興味をお持ちですか？他の人に紹介 - https://zcs1.tell-your-friend.com/ua/forward?od=11287eca74936a&rd=1328fc21093b9533&sd=1328fc21093b94d5&n=124296dffbb2ec&s=f\r\n  \r\n\r\n\r\n\r\n有限会社西尾システムコンサルタント | 神奈川県相模原市中央区陽光台3-9-12 \r\n	2024-09-24 15:48:23.099058	3
103	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/04/20 19:14に注文いただいた郷原 PC買い替え→Lenovo ノートパソコン ideaPad 320 80XR009RJPのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/04/20 19:14に注文いただいた郷原 PC買い替え→Lenovo ノートパソコン ideaPad 320 80XR009RJPのお客様に連絡する\r\n期限: 2021/01/14\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:48:38.52168	3
172	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/09/21 13:57に注文いただいたASUA 電源入れないのお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/09/21 13:57に注文いただいたASUA 電源入れないのお客様に連絡する\r\n期限: 2021/06/17\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 16:01:46.629593	3
105	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/05/01 18:10に注文いただいた山口　TOSHIBA RX3SM226Y/3HD WIN7に戻したいのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/05/01 18:10に注文いただいた山口　TOSHIBA RX3SM226Y/3HD WIN7に戻したいのお客様に連絡する\r\n期限: 2021/01/25\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:49:27.085126	3
107	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/05/01 18:10に注文いただいた山口　TOSHIBA RX3SM226Y/3HD WIN7に戻したいのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/05/01 18:10に注文いただいた山口　TOSHIBA RX3SM226Y/3HD WIN7に戻したいのお客様に連絡する\r\n期限: 2021/01/25\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:49:32.455794	3
109	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/05/01 18:10に注文いただいた山口　TOSHIBA RX3SM226Y/3HD WIN7に戻したいのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/05/01 18:10に注文いただいた山口　TOSHIBA RX3SM226Y/3HD WIN7に戻したいのお客様に連絡する\r\n期限: 2021/01/25\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:49:58.840108	3
111	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/05/07 17:46に注文いただいた前田　TOSHIBAノートPC　買い替えのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/05/07 17:46に注文いただいた前田　TOSHIBAノートPC　買い替えのお客様に連絡する\r\n期限: 2021/01/31\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:50:12.997805	3
113	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/04/10 14:42に注文いただいた薮田　買い換えのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/04/10 14:42に注文いただいた薮田　買い換えのお客様に連絡する\r\n期限: 2021/01/04\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:50:20.159545	3
115	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/05/21 09:12に注文いただいた買い替えのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/05/21 09:12に注文いただいた買い替えのお客様に連絡する\r\n期限: 2021/02/14\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:50:45.78498	3
117	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2016/09/13 20:57に注文いただいた四台パソコン預かる電話して行くのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2016/09/13 20:57に注文いただいた四台パソコン預かる電話して行くのお客様に連絡する\r\n期限: 2019/06/10\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:50:53.03254	3
119	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/05/21 09:12に注文いただいたメイプル 小林　買い替えのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/05/21 09:12に注文いただいたメイプル 小林　買い替えのお客様に連絡する\r\n期限: 2021/02/14\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:51:10.178624	3
121	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2016/09/13 20:57に注文いただいた三揮四台パソコン預かる電話して行くのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2016/09/13 20:57に注文いただいた三揮四台パソコン預かる電話して行くのお客様に連絡する\r\n期限: 2019/06/10\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:51:29.007799	3
123	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/05/31 12:01に注文いただいたおおさわ 月間IT化＆デザイン(MFから電子メール請求)のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/05/31 12:01に注文いただいたおおさわ 月間IT化＆デザイン(MFから電子メール請求)のお客様に連絡する\r\n期限: 2021/02/24\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:51:41.480983	3
106	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/05/01 18:10に注文いただいた山口　TOSHIBA RX3SM226Y/3HD WIN7に戻したいのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/05/01 18:10に注文いただいた山口　TOSHIBA RX3SM226Y/3HD WIN7に戻したいのお客様に連絡する\r\n期限: 2021/01/25\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:49:30.071391	3
108	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/05/01 18:10に注文いただいた山口　TOSHIBA RX3SM226Y/3HD WIN7に戻したいのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/05/01 18:10に注文いただいた山口　TOSHIBA RX3SM226Y/3HD WIN7に戻したいのお客様に連絡する\r\n期限: 2021/01/25\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:49:37.833103	3
110	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/05/01 18:10に注文いただいた山口　TOSHIBA RX3SM226Y/3HD WIN7に戻したいのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/05/01 18:10に注文いただいた山口　TOSHIBA RX3SM226Y/3HD WIN7に戻したいのお客様に連絡する\r\n期限: 2021/01/25\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:50:02.429009	3
112	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/04/10 14:42に注文いただいた薮田　買い換えのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/04/10 14:42に注文いただいた薮田　買い換えのお客様に連絡する\r\n期限: 2021/01/04\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:50:15.977713	3
114	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/04/10 14:42に注文いただいた薮田　買い換えのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/04/10 14:42に注文いただいた薮田　買い換えのお客様に連絡する\r\n期限: 2021/01/04\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:50:22.52886	3
116	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2016/09/13 20:57に注文いただいた四台パソコン預かる電話して行くのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2016/09/13 20:57に注文いただいた四台パソコン預かる電話して行くのお客様に連絡する\r\n期限: 2019/06/10\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:50:49.4803	3
118	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/05/21 09:12に注文いただいたメイプル 小林　買い替えのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/05/21 09:12に注文いただいたメイプル 小林　買い替えのお客様に連絡する\r\n期限: 2021/02/14\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:51:06.036994	3
120	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/05/21 09:12に注文いただいたメイプル 小林　会計用ノートPC買い替え希望のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/05/21 09:12に注文いただいたメイプル 小林　会計用ノートPC買い替え希望のお客様に連絡する\r\n期限: 2021/02/14\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:51:13.727915	3
122	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/05/24 19:23に注文いただいた相模理工　２台デスクトップPC　SSD交換とデータ取り出しのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/05/24 19:23に注文いただいた相模理工　２台デスクトップPC　SSD交換とデータ取り出しのお客様に連絡する\r\n期限: 2021/02/17\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:51:31.368381	3
124	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/05/31 12:01に注文いただいたおおさわ 月間IT化＆デザイン(MF請求 電子メール)のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/05/31 12:01に注文いただいたおおさわ 月間IT化＆デザイン(MF請求 電子メール)のお客様に連絡する\r\n期限: 2021/02/24\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:51:45.602598	3
125	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/05/31 12:01に注文いただいたおおさわ 月間IT化＆デザイン(MF請求 電子メール)のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/05/31 12:01に注文いただいたおおさわ 月間IT化＆デザイン(MF請求 電子メール)のお客様に連絡する\r\n期限: 2021/02/24\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:51:49.162601	3
126	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/06/01 00:38に注文いただいたおおさわ 月間IT化＆デザイン(MF請求 電子メール)のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/06/01 00:38に注文いただいたおおさわ 月間IT化＆デザイン(MF請求 電子メール)のお客様に連絡する\r\n期限: 2021/02/25\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:51:54.821522	3
127	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/06/01 01:02に注文いただいたおおさわ 月間IT化＆デザイン(MF請求 電子メール)のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/06/01 01:02に注文いただいたおおさわ 月間IT化＆デザイン(MF請求 電子メール)のお客様に連絡する\r\n期限: 2021/02/25\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:52:00.780804	3
128	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/06/04 20:03に注文いただいた伊藤　Office2016 personal 購入のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/06/04 20:03に注文いただいた伊藤　Office2016 personal 購入のお客様に連絡する\r\n期限: 2021/02/28\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:52:37.368704	3
129	makoto@team240.net	緊急情報　WindowsUpdate後　画面がでてこない現象が多発しています	   \r\n    \r\n         \r\n \r\n     \r\n \r\n      \r\n    \r\n   \r\n\r\n西尾 様 \r\n\r\n\r\nいつもパソコン修理でお世話になっております。 \r\n \r\n今回は緊急情報です。 \r\nWindowsUpdate後にいつまでたっても画面がでてこない事案が多発しています \r\n\r\n\r\n \r\nこんにちは \r\n西尾です \r\n先月より \r\n\r\nWindowsUpdateした。 \r\nベアリングのような模様がまわって（起動画面）いつもの画面が表示されない。 \r\n\r\n### これは最近多発しております \r\n\r\n### この場合慌てずに \r\n http://xn--tckta3d4g556n9i7b.net/2018/06/07/958  http://xn--tckta3d4g556n9i7b.net/2018/06/07/958 [ http://xn--tckta3d4g556n9i7b.net/2018/06/07/958 ]\r\n\r\n http://xn--tckta3d4g556n9i7b.net/2018/06/07/958 この方法で解決できます \r\n\r\n\r\nconnected user experiences and telemetryというサービスの不具合または相性が悪いことがあるようです \r\n\r\n当社では遠隔サポートもしております。 \r\n http://xn--tckta3d4g556n9i7b.net/contact お気軽にお問い合わせください。 \r\n\r\n http://xn--tckta3d4g556n9i7b.net/contact http://xn--tckta3d4g556n9i7b.net/contact \r\n\r\n\r\n\r\n \r\n携帯　  tel:09071761549 090-7176-1549 　にお気軽にお問い合わせください \r\n\r\n     \r\n    \r\n   \r\n       \r\n    \r\n   \r\n高機能ノートパソコン特別価格も引き続きご紹介中      \r\n       \r\n \r\n     \r\n \r\n      \r\n       \r\n \r\n     \r\n \r\n            \r\n \r\n\r\n\r\n\r\n\r\n----------------------------------------------------------------------\r\nこのメールの送信者： makoto@team240.net 宛先 makoto@team240.net\r\n\r\n興味が無い場合登録の解除 - https://zcs1.maillist-manage.com/ua/optout?od=11287eca74936a&rd=1328fc21093f61ee&sd=1328fc21093f617d&n=11699e4c24a6c0a\r\n\r\n登録情報の更新 -  https://zcs1.maillist-manage.com/ua/upc?upd=1328fc21092c2209&r=1328fc21093f61ee&n=11699e4c24a6c0a&od=11287eca74936a\r\n \r\n興味をお持ちの場合登録- https://zcs1.maillist-manage.com/ua/optin?od=11287eca74936a&rd=1328fc21093f61ee&sd=1328fc21093f617d&n=11699e4c24a6c0a\r\n  \r\n\r\n\r\n\r\n有限会社西尾システムコンサルタント | 神奈川県相模原市中央区陽光台3-9-12 \r\n\r\n\r\n	2024-09-24 15:52:44.524329	3
130	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2016/09/13 20:57に注文いただいた三揮四台パソコン預かる電話して行くのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2016/09/13 20:57に注文いただいた三揮四台パソコン預かる電話して行くのお客様に連絡する\r\n期限: 2019/06/10\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:52:50.677494	3
131	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2016/09/13 20:57に注文いただいた三揮四台パソコン預かる電話して行くのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2016/09/13 20:57に注文いただいた三揮四台パソコン預かる電話して行くのお客様に連絡する\r\n期限: 2019/06/10\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:52:54.259872	3
132	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/03/26 14:47に注文いただいた飯田 さんバイオSSD交換のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/03/26 14:47に注文いただいた飯田 さんバイオSSD交換のお客様に連絡する\r\n期限: 2020/12/20\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:53:05.1514	3
133	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/05/01 18:10に注文いただいた山口　TOSHIBA RX3SM226Y/3HD WIN7に戻したいのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/05/01 18:10に注文いただいた山口　TOSHIBA RX3SM226Y/3HD WIN7に戻したいのお客様に連絡する\r\n期限: 2021/01/25\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:53:07.527487	3
134	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2016/09/13 20:57に注文いただいた三揮四台パソコン預かる電話して行くのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2016/09/13 20:57に注文いただいた三揮四台パソコン預かる電話して行くのお客様に連絡する\r\n期限: 2019/06/10\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:53:09.309734	3
136	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/04/20 19:14に注文いただいた郷原 PC買い替え→Lenovo ノートパソコン ideaPad 320 80XR009RJPのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/04/20 19:14に注文いただいた郷原 PC買い替え→Lenovo ノートパソコン ideaPad 320 80XR009RJPのお客様に連絡する\r\n期限: 2021/01/14\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:53:12.872037	3
138	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/04/20 17:08に注文いただいた伊藤亘さんavgと買い換え相談のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/04/20 17:08に注文いただいた伊藤亘さんavgと買い換え相談のお客様に連絡する\r\n期限: 2021/01/14\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:53:18.228746	3
140	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/06/04 20:03に注文いただいた伊藤　Office2016 personal 購入のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/06/04 20:03に注文いただいた伊藤　Office2016 personal 購入のお客様に連絡する\r\n期限: 2021/02/28\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:53:23.85781	3
142	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/05/31 12:01に注文いただいたおおさわ 月間IT化＆デザイン(MF請求 電子メール)のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/05/31 12:01に注文いただいたおおさわ 月間IT化＆デザイン(MF請求 電子メール)のお客様に連絡する\r\n期限: 2021/02/24\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:53:27.450231	3
144	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2016/09/13 20:57に注文いただいた三揮四台パソコン預かる電話して行くのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2016/09/13 20:57に注文いただいた三揮四台パソコン預かる電話して行くのお客様に連絡する\r\n期限: 2019/06/10\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:53:37.06619	3
146	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2016/09/13 20:57に注文いただいた三揮四台パソコン預かる電話して行くのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2016/09/13 20:57に注文いただいた三揮四台パソコン預かる電話して行くのお客様に連絡する\r\n期限: 2019/06/10\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:53:44.920774	3
148	makoto@team240.net	緊急情報　WindowsUpdate後　画面がでてこない現象が多発しています	   \n    \n         \n \n     \n \n      \n    \n   \n\n西尾 様 \n前回の記事で主にWindows10で起きる現象の解決方法を示しました \n\n\n今回は Windows7編 ですWindows updateに失敗し、再起動ループしてしまう時などの対処方法 \nそれにはまず外部メディア（USBメモリやCD/DVD）起動でセーフモードに入ります \n\n\n　これはWindows10でも適用できるかもしれませんが \nWindows Updateの途中段階はWindowsSystem32Pending.xmlに保存されているのでこれをまず削除 \ncd C:WindowsWinSxS  \ndel Pending.xml \nこれで再起動して復旧することもあります。この場合は更新のエラーで止まっていた場合ですね \n\n\n　それでも起動しない場合はもともとシステムに不具合があるところにWindowsUpdateが始まって不具合があった場合 \nこの時はsfc /scannowというコマンドでシステムの整合性チェックを行います \n具体的には \nsfc /scannow /offbootdir=d: /offwindir=d:windows \nという様に詳細に整合性チェックするといいでしょう \nご自分で不安な方の修理のお問合せはhttp://パソコン修理.net/contactまで \n西尾システムコンサルタント　西尾 \n\n\n\n### なおブログに掲載しています \n http://xn--tckta3d4g556n9i7b.net/2018/06/07/958 http://パソコン修理.net/2018/06/10/962 \n\n\n当社では遠隔サポートもしております。 \n\n http://xn--tckta3d4g556n9i7b.net/contact お気軽にお問い合わせください。 \n\n http://xn--tckta3d4g556n9i7b.net/contact http://xn--tckta3d4g556n9i7b.net/contact \n\n\n\n \n携帯　  tel:09071761549 090-7176-1549 　にお気軽にお問い合わせください \n\n     \n    \n   \n       \n    \n   \n高機能ノートパソコン特別価格も引き続きご紹介中      \n       \n \n     \n \n      \n       \n \n     \n \n            \n \n\n\n\n\n----------------------------------------------------------------------\nこのメールの送信者： makoto@team240.net 宛先 makoto@team240.net\n\n興味が無い場合登録の解除 - https://zcs1.maillist-manage.com/ua/optout?od=11287eca74936a&rd=1328fc21093fe29f&sd=1328fc21093fe26b&n=11699e4bf3098b5\n\n登録情報の更新 -  https://zcs1.maillist-manage.com/ua/upc?upd=1328fc21092c2209&r=1328fc21093fe29f&n=11699e4bf3098b5&od=11287eca74936a\n \n興味をお持ちの場合登録- https://zcs1.maillist-manage.com/ua/optin?od=11287eca74936a&rd=1328fc21093fe29f&sd=1328fc21093fe26b&n=11699e4bf3098b5\n  \n\n\n\n有限会社西尾システムコンサルタント | 神奈川県相模原市中央区陽光台3-9-12 \n\n\n	2024-09-24 15:53:54.622246	3
150	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/06/04 20:03に注文いただいた伊藤　Office2016 personal 購入のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/06/04 20:03に注文いただいた伊藤　Office2016 personal 購入のお客様に連絡する\r\n期限: 2021/02/28\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:54:19.077302	3
135	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/05/07 17:46に注文いただいた前田　TOSHIBAノートPC　買い替えのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/05/07 17:46に注文いただいた前田　TOSHIBAノートPC　買い替えのお客様に連絡する\r\n期限: 2021/01/31\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:53:11.080773	3
137	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/04/10 14:42に注文いただいた薮田　買い換えのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/04/10 14:42に注文いただいた薮田　買い換えのお客様に連絡する\r\n期限: 2021/01/04\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:53:14.655607	3
139	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/05/24 19:23に注文いただいた相模理工　２台デスクトップPC　SSD交換とデータ取り出しのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/05/24 19:23に注文いただいた相模理工　２台デスクトップPC　SSD交換とデータ取り出しのお客様に連絡する\r\n期限: 2021/02/17\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:53:21.298312	3
141	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/06/01 01:02に注文いただいたおおさわ 月間IT化＆デザイン(MF請求 電子メール)のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/06/01 01:02に注文いただいたおおさわ 月間IT化＆デザイン(MF請求 電子メール)のお客様に連絡する\r\n期限: 2021/02/25\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:53:25.659813	3
143	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2016/09/13 20:57に注文いただいた三揮四台パソコン預かる電話して行くのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2016/09/13 20:57に注文いただいた三揮四台パソコン預かる電話して行くのお客様に連絡する\r\n期限: 2019/06/10\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:53:35.272346	3
145	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2016/09/13 20:57に注文いただいた三揮四台パソコン預かる電話して行くのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2016/09/13 20:57に注文いただいた三揮四台パソコン預かる電話して行くのお客様に連絡する\r\n期限: 2019/06/10\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:53:41.879038	3
147	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/06/08 23:53に注文いただいた三揮四台パソコン預かる電話して行くのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/06/08 23:53に注文いただいた三揮四台パソコン預かる電話して行くのお客様に連絡する\r\n期限: 2021/03/04\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:53:49.83648	3
149	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/03/26 14:47に注文いただいた飯田 さんバイオSSD交換のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/03/26 14:47に注文いただいた飯田 さんバイオSSD交換のお客様に連絡する\r\n期限: 2020/12/20\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:54:07.689703	3
151	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/06/04 20:03に注文いただいた伊藤　Office2016 personal 購入のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/06/04 20:03に注文いただいた伊藤　Office2016 personal 購入のお客様に連絡する\r\n期限: 2021/02/28\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:54:22.062881	3
153	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/06/19 10:38に注文いただいた高野 持ち運び用PC購入希望のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/06/19 10:38に注文いただいた高野 持ち運び用PC購入希望のお客様に連絡する\r\n期限: 2021/03/15\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:54:40.202051	3
152	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/06/04 20:03に注文いただいた伊藤　Office2016 personal 購入のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/06/04 20:03に注文いただいた伊藤　Office2016 personal 購入のお客様に連絡する\r\n期限: 2021/02/28\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:54:32.961334	3
154	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2016/09/13 20:57に注文いただいた麻布大学 並河先生のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2016/09/13 20:57に注文いただいた麻布大学 並河先生のお客様に連絡する\r\n期限: 2019/06/10\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 15:55:01.413661	3
156	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/07/10 08:32に注文いただいたヨコヤマ　起動しない　買い替え検討のお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/07/10 08:32に注文いただいたヨコヤマ　起動しない　買い替え検討のお客様に連絡する\r\n期限: 2021/04/05\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 15:55:56.334628	3
158	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/07/13 11:05に注文いただいた今井さんプリンタのお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/07/13 11:05に注文いただいた今井さんプリンタのお客様に連絡する\r\n期限: 2021/04/08\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 15:56:20.350349	3
160	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/07/13 11:05に注文いただいた今井さんプリンタのお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/07/13 11:05に注文いただいた今井さんプリンタのお客様に連絡する\r\n期限: 2021/04/08\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 15:56:28.511979	3
162	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/08/27 13:22に注文いただいたコンテックス　ZOHO導入紹介のお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/08/27 13:22に注文いただいたコンテックス　ZOHO導入紹介のお客様に連絡する\r\n期限: 2021/05/23\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 15:58:57.473449	3
164	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/08/17 21:43に注文いただいたPC-HZ550DAB 持ち運び用PC　電源はいらないのお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/08/17 21:43に注文いただいたPC-HZ550DAB 持ち運び用PC　電源はいらないのお客様に連絡する\r\n期限: 2021/05/13\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 15:59:19.115287	3
166	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/09/07 09:43に注文いただいたノートPC 二台 office付き(見積 請求8/31)のお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/09/07 09:43に注文いただいたノートPC 二台 office付き(見積 請求8/31)のお客様に連絡する\r\n期限: 2021/06/03\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 15:59:56.893336	3
168	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/09/07 09:43に注文いただいたノートPC 二台 office付き(見積 請求8/31)のお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/09/07 09:43に注文いただいたノートPC 二台 office付き(見積 請求8/31)のお客様に連絡する\r\n期限: 2021/06/03\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 16:00:05.449574	3
170	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/09/10 11:40に注文いただいた榎本ビールこぼした買い替えのお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/09/10 11:40に注文いただいた榎本ビールこぼした買い替えのお客様に連絡する\r\n期限: 2021/06/06\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 16:00:43.992951	3
155	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/06/30 14:12に注文いただいたコンテックス　名刺443件スキャンと整理　（データcsv交付）のお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/06/30 14:12に注文いただいたコンテックス　名刺443件スキャンと整理　（データcsv交付）のお客様に連絡する\r\n期限: 2021/03/26\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 15:55:22.485993	3
157	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/07/13 11:05に注文いただいた49,391のお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/07/13 11:05に注文いただいた49,391のお客様に連絡する\r\n期限: 2021/04/08\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 15:56:11.210551	3
159	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/07/13 11:05に注文いただいた今井さんプリンタのお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/07/13 11:05に注文いただいた今井さんプリンタのお客様に連絡する\r\n期限: 2021/04/08\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 15:56:23.369392	3
161	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/08/01 11:21に注文いただいたNEC本体電源入らないのお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/08/01 11:21に注文いただいたNEC本体電源入らないのお客様に連絡する\r\n期限: 2021/04/27\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 15:58:06.977823	3
163	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/08/27 13:22に注文いただいた株式会社コンテックス　ZOHO導入紹介料のお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/08/27 13:22に注文いただいた株式会社コンテックス　ZOHO導入紹介料のお客様に連絡する\r\n期限: 2021/05/23\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 15:59:00.467531	3
165	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/08/17 21:43に注文いただいたPC-HZ550DAB 持ち運び用PC　電源はいらないのお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/08/17 21:43に注文いただいたPC-HZ550DAB 持ち運び用PC　電源はいらないのお客様に連絡する\r\n期限: 2021/05/13\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 15:59:22.23464	3
167	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/09/07 09:43に注文いただいたノートPC 二台 office付き(見積 請求8/31)のお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/09/07 09:43に注文いただいたノートPC 二台 office付き(見積 請求8/31)のお客様に連絡する\r\n期限: 2021/06/03\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 15:59:59.336381	3
169	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/09/10 11:40に注文いただいた榎本ビールこぼした買い替えのお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/09/10 11:40に注文いただいた榎本ビールこぼした買い替えのお客様に連絡する\r\n期限: 2021/06/06\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 16:00:24.593699	3
171	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/09/10 11:40に注文いただいた榎本ビールこぼした買い替えのお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/09/10 11:40に注文いただいた榎本ビールこぼした買い替えのお客様に連絡する\r\n期限: 2021/06/06\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 16:00:57.769488	3
173	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/09/21 13:57に注文いただいたASUA 電源入れないのお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/09/21 13:57に注文いただいたASUA 電源入れないのお客様に連絡する\r\n期限: 2021/06/17\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 16:01:51.087364	3
174	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/09/21 13:57に注文いただいたASUA 電源入れないのお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/09/21 13:57に注文いただいたASUA 電源入れないのお客様に連絡する\r\n期限: 2021/06/17\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 16:01:53.695322	3
176	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/10/04 12:03に注文いただいた今井さんパソコン買い替えNAS導入のお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/10/04 12:03に注文いただいた今井さんパソコン買い替えNAS導入のお客様に連絡する\r\n期限: 2021/06/30\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 16:02:48.435854	3
178	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2016/10/27 11:55に注文いただいた木村さんメモリとSSD交換のお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2016/10/27 11:55に注文いただいた木村さんメモリとSSD交換のお客様に連絡する\r\n期限: 2019/07/24\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 16:03:15.899829	3
180	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2016/10/26 16:11に注文いただいたメディカルサイト歯科 サーバ入れ替えのお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2016/10/26 16:11に注文いただいたメディカルサイト歯科 サーバ入れ替えのお客様に連絡する\r\n期限: 2019/07/23\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 16:03:21.395488	3
182	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2016/10/27 11:55に注文いただいた木村さんメモリとSSD交換のお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2016/10/27 11:55に注文いただいた木村さんメモリとSSD交換のお客様に連絡する\r\n期限: 2019/07/24\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 16:03:29.501497	3
184	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2016/10/26 16:11に注文いただいたメディカルサイト歯科 サーバ入れ替えのお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2016/10/26 16:11に注文いただいたメディカルサイト歯科 サーバ入れ替えのお客様に連絡する\r\n期限: 2019/07/23\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 16:03:33.112147	3
186	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/10/04 12:03に注文いただいた今井さんパソコン買い替えNAS導入のお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/10/04 12:03に注文いただいた今井さんパソコン買い替えNAS導入のお客様に連絡する\r\n期限: 2021/06/30\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 16:03:37.954371	3
189	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/10/25 09:32に注文いただいたパソコン買い換えデータ移行のお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/10/25 09:32に注文いただいたパソコン買い換えデータ移行のお客様に連絡する\r\n期限: 2021/07/21\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 16:09:41.691999	3
175	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/10/04 12:03に注文いただいた今井さんパソコン買い替えNAS導入のお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/10/04 12:03に注文いただいた今井さんパソコン買い替えNAS導入のお客様に連絡する\r\n期限: 2021/06/30\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 16:02:21.207647	3
177	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/10/04 12:03に注文いただいた今井さんパソコン買い替えNAS導入のお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/10/04 12:03に注文いただいた今井さんパソコン買い替えNAS導入のお客様に連絡する\r\n期限: 2021/06/30\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 16:02:55.707689	3
179	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/10/06 10:18に注文いただいたラムダプレシジョンNAS導入のお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/10/06 10:18に注文いただいたラムダプレシジョンNAS導入のお客様に連絡する\r\n期限: 2020/07/02\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 16:03:17.747195	3
181	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/05/21 09:12に注文いただいたメイプル 小林　会計用ノートPC買い替え希望のお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/05/21 09:12に注文いただいたメイプル 小林　会計用ノートPC買い替え希望のお客様に連絡する\r\n期限: 2021/02/14\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 16:03:23.391809	3
183	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/05/21 09:12に注文いただいたメイプル 小林　会計用ノートPC買い替え希望のお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/05/21 09:12に注文いただいたメイプル 小林　会計用ノートPC買い替え希望のお客様に連絡する\r\n期限: 2021/02/14\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 16:03:31.300821	3
185	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2017/10/06 10:18に注文いただいたラムダプレシジョンNAS導入のお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2017/10/06 10:18に注文いただいたラムダプレシジョンNAS導入のお客様に連絡する\r\n期限: 2020/07/02\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 16:03:35.528324	3
187	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/09/25 10:20に注文いただいたHP デクストップ買い替えのお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/09/25 10:20に注文いただいたHP デクストップ買い替えのお客様に連絡する\r\n期限: 2021/06/21\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 16:03:56.925177	3
188	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/10/31 14:17に注文いただいたコンテックス　マイケルさんPC 入れ換えのお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/10/31 14:17に注文いただいたコンテックス　マイケルさんPC 入れ換えのお客様に連絡する\r\n期限: 2021/07/27\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 16:09:19.250066	3
190	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：ZOHO紹介する)	タスクが割り当てられました。\r\n 西尾 真言様,\r\n \r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: ZOHO&#x7d39;&#x4ecb;&#x3059;&#x308b;\r\n期限: 2018-11-19\r\n\r\nよろしくお願いします,\r\n西尾 真言	2024-09-24 16:10:22.141963	3
191	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：ルータ交換とエクセルリソースエラーどうしますか？準備ができたらご連絡ください)	タスクが割り当てられました。\r\n 西尾 真言様,\r\n \r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: &#x30eb;&#x30fc;&#x30bf;&#x4ea4;&#x63db;&#x3068;&#x30a8;&#x30af;&#x30bb;&#x30eb;&#x30ea;&#x30bd;&#x30fc;&#x30b9;&#x30a8;&#x30e9;&#x30fc;&#x3069;&#x3046;&#x3057;&#x307e;&#x3059;&#x304b;&#xff1f;&#x6e96;&#x5099;&#x304c;&#x3067;&#x304d;&#x305f;&#x3089;&#x3054;&#x9023;&#x7d61;&#x304f;&#x3060;&#x3055;&#x3044;\r\n期限: 2018-11-21\r\n\r\nよろしくお願いします,\r\n西尾 真言	2024-09-24 16:10:47.26627	3
192	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：ルータ交換とエクセルリソースエラーどうしますか？準備ができたらご連絡ください)	タスクが割り当てられました。\r\n 西尾 真言様,\r\n \r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: &#x30eb;&#x30fc;&#x30bf;&#x4ea4;&#x63db;&#x3068;&#x30a8;&#x30af;&#x30bb;&#x30eb;&#x30ea;&#x30bd;&#x30fc;&#x30b9;&#x30a8;&#x30e9;&#x30fc;&#x3069;&#x3046;&#x3057;&#x307e;&#x3059;&#x304b;&#xff1f;&#x6e96;&#x5099;&#x304c;&#x3067;&#x304d;&#x305f;&#x3089;&#x3054;&#x9023;&#x7d61;&#x304f;&#x3060;&#x3055;&#x3044;\r\n期限: 2018-11-23\r\n\r\nよろしくお願いします,\r\n西尾 真言	2024-09-24 16:10:49.406363	3
194	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：ルータ交換とエクセルリソースエラーどうしますか？準備ができたらご連絡ください)	タスクが割り当てられました。\r\n 西尾 真言様,\r\n \r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: &#x30eb;&#x30fc;&#x30bf;&#x4ea4;&#x63db;&#x3068;&#x30a8;&#x30af;&#x30bb;&#x30eb;&#x30ea;&#x30bd;&#x30fc;&#x30b9;&#x30a8;&#x30e9;&#x30fc;&#x3069;&#x3046;&#x3057;&#x307e;&#x3059;&#x304b;&#xff1f;&#x6e96;&#x5099;&#x304c;&#x3067;&#x304d;&#x305f;&#x3089;&#x3054;&#x9023;&#x7d61;&#x304f;&#x3060;&#x3055;&#x3044;\r\n期限: 2018-11-27\r\n\r\nよろしくお願いします,\r\n西尾 真言	2024-09-24 16:10:53.11049	3
196	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：ルータ交換とエクセルリソースエラーどうしますか？準備ができたらご連絡ください)	タスクが割り当てられました。\r\n 西尾 真言様,\r\n \r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: &#x30eb;&#x30fc;&#x30bf;&#x4ea4;&#x63db;&#x3068;&#x30a8;&#x30af;&#x30bb;&#x30eb;&#x30ea;&#x30bd;&#x30fc;&#x30b9;&#x30a8;&#x30e9;&#x30fc;&#x3069;&#x3046;&#x3057;&#x307e;&#x3059;&#x304b;&#xff1f;&#x6e96;&#x5099;&#x304c;&#x3067;&#x304d;&#x305f;&#x3089;&#x3054;&#x9023;&#x7d61;&#x304f;&#x3060;&#x3055;&#x3044;\r\n期限: 2018-11-28\r\n\r\nよろしくお願いします,\r\n西尾 真言	2024-09-24 16:10:56.794517	3
198	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：ルータ交換とエクセルリソースエラーどうしますか？準備ができたらご連絡ください)	タスクが割り当てられました。\r\n 西尾 真言様,\r\n \r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: &#x30eb;&#x30fc;&#x30bf;&#x4ea4;&#x63db;&#x3068;&#x30a8;&#x30af;&#x30bb;&#x30eb;&#x30ea;&#x30bd;&#x30fc;&#x30b9;&#x30a8;&#x30e9;&#x30fc;&#x3069;&#x3046;&#x3057;&#x307e;&#x3059;&#x304b;&#xff1f;&#x6e96;&#x5099;&#x304c;&#x3067;&#x304d;&#x305f;&#x3089;&#x3054;&#x9023;&#x7d61;&#x304f;&#x3060;&#x3055;&#x3044;\r\n期限: 2018-11-22\r\n\r\nよろしくお願いします,\r\n西尾 真言	2024-09-24 16:11:00.389139	3
200	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：ルータ交換とエクセルリソースエラーどうしますか？準備ができたらご連絡ください)	タスクが割り当てられました。\r\n 西尾 真言様,\r\n \r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: &#x30eb;&#x30fc;&#x30bf;&#x4ea4;&#x63db;&#x3068;&#x30a8;&#x30af;&#x30bb;&#x30eb;&#x30ea;&#x30bd;&#x30fc;&#x30b9;&#x30a8;&#x30e9;&#x30fc;&#x3069;&#x3046;&#x3057;&#x307e;&#x3059;&#x304b;&#xff1f;&#x6e96;&#x5099;&#x304c;&#x3067;&#x304d;&#x305f;&#x3089;&#x3054;&#x9023;&#x7d61;&#x304f;&#x3060;&#x3055;&#x3044;\r\n期限: 2018-11-20\r\n\r\nよろしくお願いします,\r\n西尾 真言	2024-09-24 16:11:04.157193	3
202	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/10/31 14:17に注文いただいたコンテックス　マイケルさんPC 入れ換えのお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/10/31 14:17に注文いただいたコンテックス　マイケルさんPC 入れ換えのお客様に連絡する\r\n期限: 2021/07/27\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 16:12:14.669611	3
204	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/10/30 16:48に注文いただいた諏佐 Win7→Win10 バージョンアップ HDD交換のお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/10/30 16:48に注文いただいた諏佐 Win7→Win10 バージョンアップ HDD交換のお客様に連絡する\r\n期限: 2021/07/26\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 16:13:12.856931	3
206	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/07/16 15:52に注文いただいたHP PC買い替え/NAS購入のお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/07/16 15:52に注文いただいたHP PC買い替え/NAS購入のお客様に連絡する\r\n期限: 2021/04/11\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 16:13:23.800346	3
208	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/07/16 15:52に注文いただいたHP PC買い替え/NAS購入のお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/07/16 15:52に注文いただいたHP PC買い替え/NAS購入のお客様に連絡する\r\n期限: 2021/04/11\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 16:13:30.093339	3
210	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/12/15 11:34に注文いただいた早川さん富士通ノートと筆ぐるめ購入のお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/12/15 11:34に注文いただいた早川さん富士通ノートと筆ぐるめ購入のお客様に連絡する\r\n期限: 2021/09/10\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 16:15:12.402512	3
193	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：ルータ交換とエクセルリソースエラーどうしますか？準備ができたらご連絡ください)	タスクが割り当てられました。\r\n 西尾 真言様,\r\n \r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: &#x30eb;&#x30fc;&#x30bf;&#x4ea4;&#x63db;&#x3068;&#x30a8;&#x30af;&#x30bb;&#x30eb;&#x30ea;&#x30bd;&#x30fc;&#x30b9;&#x30a8;&#x30e9;&#x30fc;&#x3069;&#x3046;&#x3057;&#x307e;&#x3059;&#x304b;&#xff1f;&#x6e96;&#x5099;&#x304c;&#x3067;&#x304d;&#x305f;&#x3089;&#x3054;&#x9023;&#x7d61;&#x304f;&#x3060;&#x3055;&#x3044;\r\n期限: 2018-11-24\r\n\r\nよろしくお願いします,\r\n西尾 真言	2024-09-24 16:10:51.255284	3
195	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：ルータ交換とエクセルリソースエラーどうしますか？準備ができたらご連絡ください)	タスクが割り当てられました。\r\n 西尾 真言様,\r\n \r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: &#x30eb;&#x30fc;&#x30bf;&#x4ea4;&#x63db;&#x3068;&#x30a8;&#x30af;&#x30bb;&#x30eb;&#x30ea;&#x30bd;&#x30fc;&#x30b9;&#x30a8;&#x30e9;&#x30fc;&#x3069;&#x3046;&#x3057;&#x307e;&#x3059;&#x304b;&#xff1f;&#x6e96;&#x5099;&#x304c;&#x3067;&#x304d;&#x305f;&#x3089;&#x3054;&#x9023;&#x7d61;&#x304f;&#x3060;&#x3055;&#x3044;\r\n期限: 2018-11-29\r\n\r\nよろしくお願いします,\r\n西尾 真言	2024-09-24 16:10:54.976668	3
197	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：ルータ交換とエクセルリソースエラーどうしますか？準備ができたらご連絡ください)	タスクが割り当てられました。\r\n 西尾 真言様,\r\n \r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: &#x30eb;&#x30fc;&#x30bf;&#x4ea4;&#x63db;&#x3068;&#x30a8;&#x30af;&#x30bb;&#x30eb;&#x30ea;&#x30bd;&#x30fc;&#x30b9;&#x30a8;&#x30e9;&#x30fc;&#x3069;&#x3046;&#x3057;&#x307e;&#x3059;&#x304b;&#xff1f;&#x6e96;&#x5099;&#x304c;&#x3067;&#x304d;&#x305f;&#x3089;&#x3054;&#x9023;&#x7d61;&#x304f;&#x3060;&#x3055;&#x3044;\r\n期限: 2018-11-26\r\n\r\nよろしくお願いします,\r\n西尾 真言	2024-09-24 16:10:58.584519	3
199	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：ルータ交換とエクセルリソースエラーどうしますか？準備ができたらご連絡ください)	タスクが割り当てられました。\r\n 西尾 真言様,\r\n \r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: &#x30eb;&#x30fc;&#x30bf;&#x4ea4;&#x63db;&#x3068;&#x30a8;&#x30af;&#x30bb;&#x30eb;&#x30ea;&#x30bd;&#x30fc;&#x30b9;&#x30a8;&#x30e9;&#x30fc;&#x3069;&#x3046;&#x3057;&#x307e;&#x3059;&#x304b;&#xff1f;&#x6e96;&#x5099;&#x304c;&#x3067;&#x304d;&#x305f;&#x3089;&#x3054;&#x9023;&#x7d61;&#x304f;&#x3060;&#x3055;&#x3044;\r\n期限: 2018-11-25\r\n\r\nよろしくお願いします,\r\n西尾 真言	2024-09-24 16:11:02.355988	3
201	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：石山若葉台　ＯＣＮメールエラー)	タスクが割り当てられました。\r\n 西尾 真言様,\r\n \r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: &#x77f3;&#x5c71;&#x82e5;&#x8449;&#x53f0;&#x3000;&#xff2f;&#xff23;&#xff2e;&#x30e1;&#x30fc;&#x30eb;&#x30a8;&#x30e9;&#x30fc;\r\n期限: 2018-11-20\r\n\r\nよろしくお願いします,\r\n西尾 真言	2024-09-24 16:11:37.760708	3
203	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/09/07 09:43に注文いただいたノートPC 二台 office付き(見積 請求8/31)のお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/09/07 09:43に注文いただいたノートPC 二台 office付き(見積 請求8/31)のお客様に連絡する\r\n期限: 2021/06/03\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 16:13:04.210655	3
205	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/08/31 10:03に注文いただいたQNAP バックアップエラー(2GBレート 容量少なくなった)のお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/08/31 10:03に注文いただいたQNAP バックアップエラー(2GBレート 容量少なくなった)のお客様に連絡する\r\n期限: 2021/05/27\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 16:13:20.673764	3
207	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/07/16 15:52に注文いただいたHP PC買い替え/NAS購入のお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/07/16 15:52に注文いただいたHP PC買い替え/NAS購入のお客様に連絡する\r\n期限: 2021/04/11\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 16:13:26.838654	3
209	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/11/19 17:16に注文いただいた池田さん中古パソコン買いたいのお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/11/19 17:16に注文いただいた池田さん中古パソコン買いたいのお客様に連絡する\r\n期限: 2021/08/15\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 16:13:42.88191	3
211	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/12/15 11:34に注文いただいた早川さん富士通ノートと筆ぐるめ購入のお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/12/15 11:34に注文いただいた早川さん富士通ノートと筆ぐるめ購入のお客様に連絡する\r\n期限: 2021/09/10\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 16:15:24.215619	3
212	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/12/15 11:34に注文いただいた早川さん富士通ノートと筆ぐるめ購入のお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/12/15 11:34に注文いただいた早川さん富士通ノートと筆ぐるめ購入のお客様に連絡する\r\n期限: 2021/09/10\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 16:15:27.278177	3
213	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：35,520円残金請求)	タスクが割り当てられました。\r\n 西尾 真言様,\r\n \r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 35,520円残金請求\r\n期限: 2018/12/31\r\n\r\nよろしくお願いします,\r\n西尾 真言	2024-09-24 16:25:26.82958	3
214	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2018/11/26 17:48に注文いただいた個人:PC買い替えのお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2018/11/26 17:48に注文いただいた個人:PC買い替えのお客様に連絡する\r\n期限: 2021/08/22\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 16:25:57.497887	3
215	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2019/01/23 18:17に注文いただいた大磯高校生徒会５万円以内のノートパソコンのお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2019/01/23 18:17に注文いただいた大磯高校生徒会５万円以内のノートパソコンのお客様に連絡する\r\n期限: 2021/10/19\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 16:27:04.07675	3
216	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2019/01/25 17:34に注文いただいたDELL PC新規購入3台のお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2019/01/25 17:34に注文いただいたDELL PC新規購入3台のお客様に連絡する\r\n期限: 2021/10/21\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 16:27:19.194668	3
217	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2019/01/29 10:40に注文いただいたWindows10バージョンアップと新規設定のお客様に連絡する)	タスクが割り当てられました。\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 買替・不具合点検をお客様にPUSHする。2019/01/29 10:40に注文いただいたWindows10バージョンアップと新規設定のお客様に連絡する\r\n期限: 2021/10/25\r\n\r\nよろしくお願いします,\r\n&#x771f;&#x8a00; &#x897f;&#x5c3e;	2024-09-24 16:27:39.099666	3
218	makoto@team240.net	次の購読の確認： 西尾システムコンサルタント	こんにちは,次へのご登録ありがとうございます： &#x897f;&#x5c3e;&#x30b7;&#x30b9;&#x30c6;&#x30e0;&#x30b3;&#x30f3;&#x30b5;&#x30eb;&#x30bf;&#x30f3;&#x30c8;. 購読を確認するには、次のボタンをクリックしてください。このオプションは、残り60日で期限が切れます。 購読の確認     購読していない場合は、このメールを無視してください。よろしくお願いします, &#x897f;&#x5c3e; &#x771f;&#x8a00;&#x897f;&#x5c3e;&#x30b7;&#x30b9;&#x30c6;&#x30e0;&#x30b3;&#x30f3;&#x30b5;&#x30eb;&#x30bf;&#x30f3;&#x30c8;. このメールは送信専用アドレスから送信されています。返信しないでください。	2024-09-24 16:34:16.688113	3
219	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2019/01/29 10:40に注文いただいたWindows10バージョンアップと新規設定のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: &#x8cb7;&#x66ff;&#x30fb;&#x4e0d;&#x5177;&#x5408;&#x70b9;&#x691c;&#x3092;&#x304a;&#x5ba2;&#x69d8;&#x306b;PUSH&#x3059;&#x308b;&#x3002;2019&#x2f;01&#x2f;29 10&#x3a;40&#x306b;&#x6ce8;&#x6587;&#x3044;&#x305f;&#x3060;&#x3044;&#x305f;Windows10&#x30d0;&#x30fc;&#x30b8;&#x30e7;&#x30f3;&#x30a2;&#x30c3;&#x30d7;&#x3068;&#x65b0;&#x898f;&#x8a2d;&#x5b9a;&#x306e;&#x304a;&#x5ba2;&#x69d8;&#x306b;&#x9023;&#x7d61;&#x3059;&#x308b;\r\n期限: 2021/10/25\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 16:44:26.099066	3
220	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2019/01/31 22:57に注文いただいたDELL もう一台追加購入のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: &#x8cb7;&#x66ff;&#x30fb;&#x4e0d;&#x5177;&#x5408;&#x70b9;&#x691c;&#x3092;&#x304a;&#x5ba2;&#x69d8;&#x306b;PUSH&#x3059;&#x308b;&#x3002;2019&#x2f;01&#x2f;31 22&#x3a;57&#x306b;&#x6ce8;&#x6587;&#x3044;&#x305f;&#x3060;&#x3044;&#x305f;DELL &#x3082;&#x3046;&#x4e00;&#x53f0;&#x8ffd;&#x52a0;&#x8cfc;&#x5165;&#x306e;&#x304a;&#x5ba2;&#x69d8;&#x306b;&#x9023;&#x7d61;&#x3059;&#x308b;\r\n期限: 2021/10/27\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 16:44:29.0645	3
221	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2019/01/29 10:40に注文いただいたWindows10バージョンアップと新規設定のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: &#x8cb7;&#x66ff;&#x30fb;&#x4e0d;&#x5177;&#x5408;&#x70b9;&#x691c;&#x3092;&#x304a;&#x5ba2;&#x69d8;&#x306b;PUSH&#x3059;&#x308b;&#x3002;2019&#x2f;01&#x2f;29 10&#x3a;40&#x306b;&#x6ce8;&#x6587;&#x3044;&#x305f;&#x3060;&#x3044;&#x305f;Windows10&#x30d0;&#x30fc;&#x30b8;&#x30e7;&#x30f3;&#x30a2;&#x30c3;&#x30d7;&#x3068;&#x65b0;&#x898f;&#x8a2d;&#x5b9a;&#x306e;&#x304a;&#x5ba2;&#x69d8;&#x306b;&#x9023;&#x7d61;&#x3059;&#x308b;\r\n期限: 2021/10/25\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 16:44:33.258332	3
222	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2019/01/29 10:40に注文いただいた田中　Windows10バージョンアップと新規設定のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: &#x8cb7;&#x66ff;&#x30fb;&#x4e0d;&#x5177;&#x5408;&#x70b9;&#x691c;&#x3092;&#x304a;&#x5ba2;&#x69d8;&#x306b;PUSH&#x3059;&#x308b;&#x3002;2019&#x2f;01&#x2f;29 10&#x3a;40&#x306b;&#x6ce8;&#x6587;&#x3044;&#x305f;&#x3060;&#x3044;&#x305f;&#x7530;&#x4e2d;&#x3000;Windows10&#x30d0;&#x30fc;&#x30b8;&#x30e7;&#x30f3;&#x30a2;&#x30c3;&#x30d7;&#x3068;&#x65b0;&#x898f;&#x8a2d;&#x5b9a;&#x306e;&#x304a;&#x5ba2;&#x69d8;&#x306b;&#x9023;&#x7d61;&#x3059;&#x308b;\r\n期限: 2021/10/25\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 16:44:37.648398	3
224	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2019/02/20 22:14に注文いただいたROLE　席MAP制作のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: &#x8cb7;&#x66ff;&#x30fb;&#x4e0d;&#x5177;&#x5408;&#x70b9;&#x691c;&#x3092;&#x304a;&#x5ba2;&#x69d8;&#x306b;PUSH&#x3059;&#x308b;&#x3002;2019&#x2f;02&#x2f;20 22&#x3a;14&#x306b;&#x6ce8;&#x6587;&#x3044;&#x305f;&#x3060;&#x3044;&#x305f;ROLE&#x3000;&#x5e2d;MAP&#x5236;&#x4f5c;&#x306e;&#x304a;&#x5ba2;&#x69d8;&#x306b;&#x9023;&#x7d61;&#x3059;&#x308b;\r\n期限: 2021/11/16\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 16:45:34.030487	3
226	makoto@team240.net	Zoho Show	<div style='background-color: #ececec; padding:20px 0; font-family: Lucida Grande, Segoe UI, Arial, sans-serif;font-size: 12px;'><div style='width:740px; min-height:220px; margin:30px auto; -webkit-box-shadow:0px 0px 8px #d5d5d5; -moz-box-shadow:0px 0px 8px #d5d5d5; -ms-box-shadow:0px 0px 8px #d5d5d5; box-shadow:0px 0px 8px #d5d5d5; -ms-filter: progid:DXImageTransform.Microsoft.Shadow(Strength=8, Direction=135, Color=#d5d5d5); filter: progid:DXImageTransform.Microsoft.Shadow(Strength=5, Direction=135, Color=#d5d5d5); padding-top:1px; background-color:#E38D25;'><div style='min-height:400px;margin-left:8px;width:732px;background-color:#fff;'><div style='height:85px;'><img style='float: right; margin: 28px 55px 0 0;' width='128' height='24' src='https://img.zohostatic.com/show/EXP_2/styles/images/showlogo.png' title='Zoho ショー' alt='Zoho ショー' /></div><div style='min-height: 50px; padding: 0 55px;margin: 0; line-height: 1.5em;'>makotoさん<br><br>西尾真言さんがプレゼンテーション（日本に紹介！　保康生醫股份有限公司）を閲覧するよう依頼しています。プレゼンテーションを閲覧するには、下のリンクをクリックしてください。<br><br>https://show.zoho.com/show/publish/5ehzk89306cca4594419b9a6a76ba8001ef8f<br><br>Zoho ショーについての詳細は、show.zoho.comをご確認ください。不明な点がある場合は、support@zohoshow.comまでお問い合わせください。<br><br>よろしくお願いいたします。<br>Zoho ショーチーム<br>よろしくお願いします。<br/>Zoho ショーチーム</div><div style='margin: 0 auto;padding: 50px 0 5px 0;'><div style='margin: 0 auto; margin-bottom:10px; width:440px; height:1px; border-top:1px solid #f5f5f5; border-bottom: 1px solid #f5f5f5;'></div>このメールは「Zoho ショー」サービスを利用して送信されています。このメールに心当たりがなく、迷惑メールだと判断した場合、下記までご連絡ください。［お問い合わせ先］ゾーホージャパン株式会社 Zoho事業部 http://www.zoho.jp/contact/</div></div></div></div>\r\n	2024-09-24 16:46:13.234166	3
228	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：確定申告後　買い替え検討中　ご連絡お待ちしています)	タスクが割り当てられました。\r\n 西尾 真言様,\r\n \r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 確定申告後　買い替え検討中　ご連絡お待ちしています\r\n期限: 2019-03-12\r\n\r\nよろしくお願いします,\r\n西尾 真言	2024-09-24 16:46:50.761179	3
230	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：確定申告後　買い替え検討中　ご連絡お待ちしています)	タスクが割り当てられました。\r\n 西尾 真言様,\r\n \r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 確定申告後　買い替え検討中　ご連絡お待ちしています\r\n期限: 2019-03-19\r\n\r\nよろしくお願いします,\r\n西尾 真言	2024-09-24 16:46:54.243578	3
232	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2019/03/13 14:54に注文いただいた小林さんファーストオート中古パソコンのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: &#x8cb7;&#x66ff;&#x30fb;&#x4e0d;&#x5177;&#x5408;&#x70b9;&#x691c;&#x3092;&#x304a;&#x5ba2;&#x69d8;&#x306b;PUSH&#x3059;&#x308b;&#x3002;2019&#x2f;03&#x2f;13 14&#x3a;54&#x306b;&#x6ce8;&#x6587;&#x3044;&#x305f;&#x3060;&#x3044;&#x305f;&#x5c0f;&#x6797;&#x3055;&#x3093;&#x30d5;&#x30a1;&#x30fc;&#x30b9;&#x30c8;&#x30aa;&#x30fc;&#x30c8;&#x4e2d;&#x53e4;&#x30d1;&#x30bd;&#x30b3;&#x30f3;&#x306e;&#x304a;&#x5ba2;&#x69d8;&#x306b;&#x9023;&#x7d61;&#x3059;&#x308b;\r\n期限: 2021/12/07\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 16:47:34.001535	3
234	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2019/03/13 15:17に注文いただいたHPデスクトップ　2ZX70AV-ACCZ/OP/U 購入のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: &#x8cb7;&#x66ff;&#x30fb;&#x4e0d;&#x5177;&#x5408;&#x70b9;&#x691c;&#x3092;&#x304a;&#x5ba2;&#x69d8;&#x306b;PUSH&#x3059;&#x308b;&#x3002;2019&#x2f;03&#x2f;13 15&#x3a;17&#x306b;&#x6ce8;&#x6587;&#x3044;&#x305f;&#x3060;&#x3044;&#x305f;HP&#x30c7;&#x30b9;&#x30af;&#x30c8;&#x30c3;&#x30d7;&#x3000;2ZX70AV-ACCZ&#x2f;OP&#x2f;U &#x8cfc;&#x5165;&#x306e;&#x304a;&#x5ba2;&#x69d8;&#x306b;&#x9023;&#x7d61;&#x3059;&#x308b;\r\n期限: 2021/12/07\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 16:47:42.111486	3
236	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：小林さん中古３万円ノートパソコン準備します)	タスクが割り当てられました。\r\n 西尾 真言様,\r\n \r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 小林さん中古３万円ノートパソコン準備します\r\n期限: 2019-03-15\r\n\r\nよろしくお願いします,\r\n西尾 真言	2024-09-24 16:47:54.004768	3
239	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2019/03/25 11:58に注文いただいた中古デスクトップＪＷＣＡＤインストールのお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: &#x8cb7;&#x66ff;&#x30fb;&#x4e0d;&#x5177;&#x5408;&#x70b9;&#x691c;&#x3092;&#x304a;&#x5ba2;&#x69d8;&#x306b;PUSH&#x3059;&#x308b;&#x3002;2019&#x2f;03&#x2f;25 11&#x3a;58&#x306b;&#x6ce8;&#x6587;&#x3044;&#x305f;&#x3060;&#x3044;&#x305f;&#x4e2d;&#x53e4;&#x30c7;&#x30b9;&#x30af;&#x30c8;&#x30c3;&#x30d7;&#xff2a;&#xff37;&#xff23;&#xff21;&#xff24;&#x30a4;&#x30f3;&#x30b9;&#x30c8;&#x30fc;&#x30eb;&#x306e;&#x304a;&#x5ba2;&#x69d8;&#x306b;&#x9023;&#x7d61;&#x3059;&#x308b;\r\n期限: 2021/12/19\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 16:49:16.074258	3
223	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2019/02/18 22:54に注文いただいたApple　タブレット　iPad 9.7インチ　Wi-Fiモデル　32GB　シルバー　2018年春モデル　MR7G2J/A のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: &#x8cb7;&#x66ff;&#x30fb;&#x4e0d;&#x5177;&#x5408;&#x70b9;&#x691c;&#x3092;&#x304a;&#x5ba2;&#x69d8;&#x306b;PUSH&#x3059;&#x308b;&#x3002;2019&#x2f;02&#x2f;18 22&#x3a;54&#x306b;&#x6ce8;&#x6587;&#x3044;&#x305f;&#x3060;&#x3044;&#x305f;Apple&#x3000;&#x30bf;&#x30d6;&#x30ec;&#x30c3;&#x30c8;&#x3000;iPad 9.7&#x30a4;&#x30f3;&#x30c1;&#x3000;Wi-Fi&#x30e2;&#x30c7;&#x30eb;&#x3000;32GB&#x3000;&#x30b7;&#x30eb;&#x30d0;&#x30fc;&#x3000;2018&#x5e74;&#x6625;&#x30e2;&#x30c7;&#x30eb;&#x3000;MR7G2J&#x2f;A &#x306e;&#x304a;&#x5ba2;&#x69d8;&#x306b;&#x9023;&#x7d61;&#x3059;&#x308b;\r\n期限: 2021/11/14\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 16:45:26.697539	3
225	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2019/02/20 22:14に注文いただいたROLE　席MAP制作のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: &#x8cb7;&#x66ff;&#x30fb;&#x4e0d;&#x5177;&#x5408;&#x70b9;&#x691c;&#x3092;&#x304a;&#x5ba2;&#x69d8;&#x306b;PUSH&#x3059;&#x308b;&#x3002;2019&#x2f;02&#x2f;20 22&#x3a;14&#x306b;&#x6ce8;&#x6587;&#x3044;&#x305f;&#x3060;&#x3044;&#x305f;ROLE&#x3000;&#x5e2d;MAP&#x5236;&#x4f5c;&#x306e;&#x304a;&#x5ba2;&#x69d8;&#x306b;&#x9023;&#x7d61;&#x3059;&#x308b;\r\n期限: 2021/11/16\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 16:45:52.832616	3
227	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2019/02/18 21:54に注文いただいたApple　タブレット　iPad 9.7インチ　Wi-Fiモデル　32GB　シルバー　2018年春モデル　MR7G2J/A のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: &#x8cb7;&#x66ff;&#x30fb;&#x4e0d;&#x5177;&#x5408;&#x70b9;&#x691c;&#x3092;&#x304a;&#x5ba2;&#x69d8;&#x306b;PUSH&#x3059;&#x308b;&#x3002;2019&#x2f;02&#x2f;18 21&#x3a;54&#x306b;&#x6ce8;&#x6587;&#x3044;&#x305f;&#x3060;&#x3044;&#x305f;Apple&#x3000;&#x30bf;&#x30d6;&#x30ec;&#x30c3;&#x30c8;&#x3000;iPad 9.7&#x30a4;&#x30f3;&#x30c1;&#x3000;Wi-Fi&#x30e2;&#x30c7;&#x30eb;&#x3000;32GB&#x3000;&#x30b7;&#x30eb;&#x30d0;&#x30fc;&#x3000;2018&#x5e74;&#x6625;&#x30e2;&#x30c7;&#x30eb;&#x3000;MR7G2J&#x2f;A &#x306e;&#x304a;&#x5ba2;&#x69d8;&#x306b;&#x9023;&#x7d61;&#x3059;&#x308b;\r\n期限: 2021/11/14\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 16:46:44.614333	3
229	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：確定申告後　買い替え検討中　ご連絡お待ちしています)	タスクが割り当てられました。\r\n 西尾 真言様,\r\n \r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 確定申告後　買い替え検討中　ご連絡お待ちしています\r\n期限: 2019-03-05\r\n\r\nよろしくお願いします,\r\n西尾 真言	2024-09-24 16:46:52.500691	3
231	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：小林さん中古３万円ノートパソコン準備します)	タスクが割り当てられました。\r\n 西尾 真言様,\r\n \r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: 小林さん中古３万円ノートパソコン準備します\r\n期限: 2019-03-30\r\n\r\nよろしくお願いします,\r\n西尾 真言	2024-09-24 16:47:31.013416	3
233	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2019/03/13 15:17に注文いただいたHPデスクトップ　2ZX70AV-ACCZ/OP/U 購入のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: &#x8cb7;&#x66ff;&#x30fb;&#x4e0d;&#x5177;&#x5408;&#x70b9;&#x691c;&#x3092;&#x304a;&#x5ba2;&#x69d8;&#x306b;PUSH&#x3059;&#x308b;&#x3002;2019&#x2f;03&#x2f;13 15&#x3a;17&#x306b;&#x6ce8;&#x6587;&#x3044;&#x305f;&#x3060;&#x3044;&#x305f;HP&#x30c7;&#x30b9;&#x30af;&#x30c8;&#x30c3;&#x30d7;&#x3000;2ZX70AV-ACCZ&#x2f;OP&#x2f;U &#x8cfc;&#x5165;&#x306e;&#x304a;&#x5ba2;&#x69d8;&#x306b;&#x9023;&#x7d61;&#x3059;&#x308b;\r\n期限: 2021/12/07\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 16:47:39.713832	3
235	makoto@team240.net	WEBよりお問い合わせがありました	<div>WEBよりお問い合わせがありました<br /></div><br /><table style="font-size:13px"> <tr><td valign="top">お名前</td><td valign="top">:</td><td valign="top">Makoto,Nishio</td></tr><tr><td valign="top">メールアドレス</td><td valign="top">:</td><td valign="top">mac_nishio@yahoo.co.jp</td></tr><tr><td valign="top">お問い合わせ内容をお書きください</td><td valign="top">:</td><td valign="top">日本desu</td></tr></table>\r\n	2024-09-24 16:47:47.159393	3
237	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2019/03/16 16:31に注文いただいた今村さんノートパソコン購入のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: &#x8cb7;&#x66ff;&#x30fb;&#x4e0d;&#x5177;&#x5408;&#x70b9;&#x691c;&#x3092;&#x304a;&#x5ba2;&#x69d8;&#x306b;PUSH&#x3059;&#x308b;&#x3002;2019&#x2f;03&#x2f;16 16&#x3a;31&#x306b;&#x6ce8;&#x6587;&#x3044;&#x305f;&#x3060;&#x3044;&#x305f;&#x4eca;&#x6751;&#x3055;&#x3093;&#x30ce;&#x30fc;&#x30c8;&#x30d1;&#x30bd;&#x30b3;&#x30f3;&#x8cfc;&#x5165;&#x306e;&#x304a;&#x5ba2;&#x69d8;&#x306b;&#x9023;&#x7d61;&#x3059;&#x308b;\r\n期限: 2021/12/10\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 16:48:26.829216	3
238	makoto@team240.net	Zoho CRM - 新しいタスクが作成されました（件名：買替・不具合点検をお客様にPUSHする。2019/03/21 14:01に注文いただいたポータルテスト商談のお客様に連絡する)	タスクが割り当てられました。\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;さん,\r\n\r\nあなたにタスクが割り当てられました。タスクの詳細情報は次のとおりです\r\n\r\n件名: &#x8cb7;&#x66ff;&#x30fb;&#x4e0d;&#x5177;&#x5408;&#x70b9;&#x691c;&#x3092;&#x304a;&#x5ba2;&#x69d8;&#x306b;PUSH&#x3059;&#x308b;&#x3002;2019&#x2f;03&#x2f;21 14&#x3a;01&#x306b;&#x6ce8;&#x6587;&#x3044;&#x305f;&#x3060;&#x3044;&#x305f;&#x30dd;&#x30fc;&#x30bf;&#x30eb;&#x30c6;&#x30b9;&#x30c8;&#x5546;&#x8ac7;&#x306e;&#x304a;&#x5ba2;&#x69d8;&#x306b;&#x9023;&#x7d61;&#x3059;&#x308b;\r\n期限: 2021/12/15\r\n\r\nよろしくお願いします,\r\n&#x897f;&#x5c3e; &#x771f;&#x8a00;	2024-09-24 16:48:57.324975	3
\.


--
-- Data for Name: leads; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.leads (id, name, email, phone, status, created_at, last_contact, last_followup_email, last_followup_tracking_id, last_email_opened, user_id, score) FROM stdin;
1	西尾真言	macnishio@gmail.com	09071761549	New	2024-09-23 20:44:25.885257	2024-09-23 20:47:18.830673	2024-09-23 20:47:17.643286	8890efcd-0abb-4159-8ec3-dacf58d504cb	\N	1	10
2	林明慧	darkare0323@gmail.com	042-752-5536	New	2024-09-23 21:36:28.964971	2024-09-23 21:36:28.963489	\N	\N	\N	1	10
3	西尾真言	makoto@team240.net	09071761549	New	2024-09-24 11:19:35.56544	2024-09-24 11:20:05.491488	2024-09-24 11:20:04.302171	151c7438-6608-41a2-a8ac-de3744b12e57	\N	1	10
4	Zoho Support	support-zohocorp@zohosupport.com		New	2024-09-24 11:28:00.900469	2024-09-24 11:28:00.899982	\N	\N	\N	1	10
5	斉藤麻里子	yksb58.uw@gmail.com		New	2024-09-24 16:54:48.851137	2024-09-24 16:54:48.850226	\N	\N	\N	1	10
\.


--
-- Data for Name: opportunities; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.opportunities (id, name, amount, stage, close_date, created_at, user_id, account_id, lead_id) FROM stdin;
1	西尾システムコンサルタントZoho導入支援	2000000	Prospecting	2024-10-10 00:00:00	2024-09-23 22:03:02.420645	1	1	1
2	西尾勝代リフォーム	12000000	Negotiation	2024-10-04 00:00:00	2024-09-23 22:54:23.741467	1	1	2
\.


--
-- Data for Name: schedules; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.schedules (id, title, description, start_time, end_time, user_id, account_id, lead_id, opportunity_id) FROM stdin;
1	Ttes	tesh	2024-09-24 05:48:00	2024-09-24 06:48:00	1	1	1	\N
\.


--
-- Data for Name: tasks; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.tasks (id, title, description, due_date, completed, created_at, user_id, lead_id, opportunity_id, account_id) FROM stdin;
1	Zoho test task	Create Zoho test task	2024-09-24 05:45:00	t	2024-09-23 20:45:30.412668	1	1	\N	\N
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.users (id, username, email, password_hash, role) FROM stdin;
1	makoto	makoto@team240.net	pbkdf2:sha256:260000$KhisrwOPnMWzy9yV$f30fc01301dc11c25543867a6dac7e829480be0fe64f4929cc3a329fec35e301	user
\.


--
-- Name: accounts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.accounts_id_seq', 1, true);


--
-- Name: emails_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.emails_id_seq', 239, true);


--
-- Name: leads_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.leads_id_seq', 5, true);


--
-- Name: opportunities_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.opportunities_id_seq', 2, true);


--
-- Name: schedules_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.schedules_id_seq', 1, true);


--
-- Name: tasks_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.tasks_id_seq', 1, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.users_id_seq', 1, true);


--
-- Name: accounts accounts_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.accounts
    ADD CONSTRAINT accounts_pkey PRIMARY KEY (id);


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: emails emails_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.emails
    ADD CONSTRAINT emails_pkey PRIMARY KEY (id);


--
-- Name: leads leads_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.leads
    ADD CONSTRAINT leads_pkey PRIMARY KEY (id);


--
-- Name: opportunities opportunities_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.opportunities
    ADD CONSTRAINT opportunities_pkey PRIMARY KEY (id);


--
-- Name: schedules schedules_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.schedules
    ADD CONSTRAINT schedules_pkey PRIMARY KEY (id);


--
-- Name: tasks tasks_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_pkey PRIMARY KEY (id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: accounts accounts_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.accounts
    ADD CONSTRAINT accounts_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: emails emails_lead_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.emails
    ADD CONSTRAINT emails_lead_id_fkey FOREIGN KEY (lead_id) REFERENCES public.leads(id);


--
-- Name: leads leads_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.leads
    ADD CONSTRAINT leads_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: opportunities opportunities_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.opportunities
    ADD CONSTRAINT opportunities_account_id_fkey FOREIGN KEY (account_id) REFERENCES public.accounts(id);


--
-- Name: opportunities opportunities_lead_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.opportunities
    ADD CONSTRAINT opportunities_lead_id_fkey FOREIGN KEY (lead_id) REFERENCES public.leads(id);


--
-- Name: opportunities opportunities_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.opportunities
    ADD CONSTRAINT opportunities_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: schedules schedules_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.schedules
    ADD CONSTRAINT schedules_account_id_fkey FOREIGN KEY (account_id) REFERENCES public.accounts(id);


--
-- Name: schedules schedules_lead_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.schedules
    ADD CONSTRAINT schedules_lead_id_fkey FOREIGN KEY (lead_id) REFERENCES public.leads(id);


--
-- Name: schedules schedules_opportunity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.schedules
    ADD CONSTRAINT schedules_opportunity_id_fkey FOREIGN KEY (opportunity_id) REFERENCES public.opportunities(id);


--
-- Name: schedules schedules_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.schedules
    ADD CONSTRAINT schedules_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: tasks tasks_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_account_id_fkey FOREIGN KEY (account_id) REFERENCES public.accounts(id);


--
-- Name: tasks tasks_lead_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_lead_id_fkey FOREIGN KEY (lead_id) REFERENCES public.leads(id);


--
-- Name: tasks tasks_opportunity_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_opportunity_id_fkey FOREIGN KEY (opportunity_id) REFERENCES public.opportunities(id);


--
-- Name: tasks tasks_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.tasks
    ADD CONSTRAINT tasks_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: public; Owner: cloud_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE cloud_admin IN SCHEMA public GRANT ALL ON SEQUENCES TO neon_superuser WITH GRANT OPTION;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: public; Owner: cloud_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE cloud_admin IN SCHEMA public GRANT ALL ON TABLES TO neon_superuser WITH GRANT OPTION;


--
-- PostgreSQL database dump complete
--

