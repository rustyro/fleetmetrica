from cli.service import CLI, parser


parsed_args = parser.parse_args()


CLI(parsed_args).run()
